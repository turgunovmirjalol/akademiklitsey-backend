from rest_framework import generics, filters, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.pagination import PageNumberPagination
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from accounts.permissions import IsAdminOrReadOnly
from .models import GalleryAlbum, GalleryPhoto, UsefulLink, InfrastructureItem, Video
from .serializers import (
    GalleryAlbumSerializer,
    GalleryAlbumDetailSerializer,
    GalleryAlbumWriteSerializer,
    GalleryPhotoSerializer,
    GalleryPhotoUploadSerializer,
    GalleryPhotoBulkUploadSerializer,
    UsefulLinkSerializer,
    UsefulLinkWriteSerializer,
    InfrastructureItemSerializer,
    InfrastructureItemWriteSerializer,
    VideoSerializer,
    VideoWriteSerializer,
    apply_lang_filter,
)

# ─── Swagger parameters ─────────────────────────────────────────────────────

LANG_PARAM = openapi.Parameter(
    'lang', openapi.IN_QUERY,
    description="Filter response language: uz | ru",
    type=openapi.TYPE_STRING,
    enum=['uz', 'ru'],
    required=False,
)


# ─── Pagination ──────────────────────────────────────────────────────────────

class GalleryPagination(PageNumberPagination):
    page_size = 12
    page_size_query_param = 'page_size'
    max_page_size = 100


# ─────────────────────────────────────────────────────────────────────────────
# GalleryAlbum
# ─────────────────────────────────────────────────────────────────────────────

class GalleryAlbumListView(generics.ListCreateAPIView):
    """Album list and create."""
    permission_classes = [IsAdminOrReadOnly]
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    pagination_class = GalleryPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_active', 'event_date']
    search_fields = ['title_uz', 'title_ru', 'description_uz', 'description_ru']
    ordering_fields = ['sort_order', 'created_at', 'event_date', 'photos_count']
    ordering = ['sort_order', '-created_at']

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return GalleryAlbum.objects.none()
        qs = GalleryAlbum.objects.all()
        # Regular users only see active albums
        is_admin = (
            self.request.user.is_authenticated
            and hasattr(self.request.user, 'is_admin_role')
            and self.request.user.is_admin_role()
        )
        if not is_admin:
            qs = qs.filter(is_active=True)
        return qs

    def get_serializer_class(self):
        if getattr(self, 'swagger_fake_view', False):
            return GalleryAlbumSerializer
        return GalleryAlbumWriteSerializer if self.request.method == 'POST' else GalleryAlbumSerializer

    @swagger_auto_schema(
        operation_summary="Gallery albums list",
        operation_description=(
            "All gallery albums.\n\n"
            "Filters:\n"
            "- `?is_active=true|false` (for admin)\n"
            "- `?event_date=YYYY-MM-DD`\n"
            "- `?search=...` — search by name/description\n"
            "- `?ordering=sort_order|-created_at|photos_count`\n"
            "- `?lang=uz|ru` — show only that language translation"
        ),
        manual_parameters=[LANG_PARAM],
        responses={200: GalleryAlbumSerializer(many=True)},
        tags=["Gallery - Albums"],
    )
    def get(self, request, *args, **kwargs):
        lang = request.query_params.get('lang')
        qs = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(qs)
        if page is not None:
            data = GalleryAlbumSerializer(page, many=True, context={'request': request}).data
            return self.get_paginated_response(apply_lang_filter(list(data), lang))
        data = GalleryAlbumSerializer(qs, many=True, context={'request': request}).data
        return Response(apply_lang_filter(list(data), lang))

    @swagger_auto_schema(
        operation_summary="Create new album",
        operation_description=(
            "Admin only. Sent via **`multipart/form-data`**.\n\n"
            "Fields for each language are sent separately.\n"
            "At least one language `title_*` must be filled.\n\n"
            "**Important:** Use `Content-Type: multipart/form-data` for image upload.\n"
            "Cannot upload images with JSON."
        ),
        manual_parameters=[
            openapi.Parameter('title_uz', openapi.IN_FORM, type=openapi.TYPE_STRING, required=True, description="Album name (UZ)"),
            openapi.Parameter('title_ru', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="Album name (RU)"),
            openapi.Parameter('description_uz', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="Description (UZ)"),
            openapi.Parameter('description_ru', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="Description (RU)"),
            openapi.Parameter('cover_image', openapi.IN_FORM, type=openapi.TYPE_FILE, required=False, description="Cover image"),
            openapi.Parameter('event_date', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="Event date (YYYY-MM-DD)"),
            openapi.Parameter('is_active', openapi.IN_FORM, type=openapi.TYPE_BOOLEAN, required=False, default=True),
            openapi.Parameter('sort_order', openapi.IN_FORM, type=openapi.TYPE_INTEGER, required=False, default=0),
        ],
        consumes=['multipart/form-data'],
        responses={
            201: GalleryAlbumDetailSerializer,
            400: openapi.Response(description="Validation error"),
        },
        tags=["Gallery - Albums"],
    )
    def post(self, request, *args, **kwargs):
        serializer = GalleryAlbumWriteSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        album = serializer.save()
        return Response(
            GalleryAlbumDetailSerializer(album, context={'request': request}).data,
            status=status.HTTP_201_CREATED,
        )


class GalleryAlbumDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Single album — view (with photos), edit, delete."""
    permission_classes = [IsAdminOrReadOnly]
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    lookup_field = 'slug'

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return GalleryAlbum.objects.none()
        return GalleryAlbum.objects.prefetch_related('photos').all()

    def get_serializer_class(self):
        if getattr(self, 'swagger_fake_view', False):
            return GalleryAlbumDetailSerializer
        if self.request.method in ('PUT', 'PATCH'):
            return GalleryAlbumWriteSerializer
        return GalleryAlbumDetailSerializer

    def get_object(self):
        obj = get_object_or_404(
            GalleryAlbum.objects.prefetch_related('photos'),
            slug=self.kwargs['slug'],
        )
        is_admin = (
            self.request.user.is_authenticated
            and hasattr(self.request.user, 'is_admin_role')
            and self.request.user.is_admin_role()
        )
        if not obj.is_active and not is_admin:
            from rest_framework.exceptions import NotFound
            raise NotFound("This album was not found.")
        self.check_object_permissions(self.request, obj)
        return obj

    @swagger_auto_schema(
        operation_summary="Album detail (with photos)",
        operation_description="Single album with all its photos. Use ?lang= for language filter.",
        manual_parameters=[LANG_PARAM],
        responses={200: GalleryAlbumDetailSerializer, 404: openapi.Response(description="Not found")},
        tags=["Gallery - Albums"],
    )
    def get(self, request, *args, **kwargs):
        obj = self.get_object()
        lang = request.query_params.get('lang')
        data = GalleryAlbumDetailSerializer(obj, context={'request': request}).data
        return Response(apply_lang_filter(data, lang))

    @swagger_auto_schema(
        operation_summary="Update album completely",
        operation_description="Admin only. Sent via **`multipart/form-data`**.",
        manual_parameters=[
            openapi.Parameter('title_uz', openapi.IN_FORM, type=openapi.TYPE_STRING, required=True, description="Album name (UZ)"),
            openapi.Parameter('title_ru', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="Album name (RU)"),
            openapi.Parameter('description_uz', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="Description (UZ)"),
            openapi.Parameter('description_ru', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="Description (RU)"),
            openapi.Parameter('cover_image', openapi.IN_FORM, type=openapi.TYPE_FILE, required=False, description="Cover image"),
            openapi.Parameter('event_date', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="Event date (YYYY-MM-DD)"),
            openapi.Parameter('is_active', openapi.IN_FORM, type=openapi.TYPE_BOOLEAN, required=False),
            openapi.Parameter('sort_order', openapi.IN_FORM, type=openapi.TYPE_INTEGER, required=False),
        ],
        consumes=['multipart/form-data'],
        responses={200: GalleryAlbumDetailSerializer},
        tags=["Gallery - Albums"],
    )
    def put(self, request, *args, **kwargs):
        obj = self.get_object()
        serializer = GalleryAlbumWriteSerializer(obj, data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        obj = serializer.save()
        return Response(GalleryAlbumDetailSerializer(obj, context={'request': request}).data)

    @swagger_auto_schema(
        operation_summary="Update album partially",
        operation_description="Admin only. Only modified fields. **`multipart/form-data`**.",
        manual_parameters=[
            openapi.Parameter('title_uz', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="Album name (UZ)"),
            openapi.Parameter('title_ru', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="Album name (RU)"),
            openapi.Parameter('description_uz', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="Description (UZ)"),
            openapi.Parameter('description_ru', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="Description (RU)"),
            openapi.Parameter('cover_image', openapi.IN_FORM, type=openapi.TYPE_FILE, required=False, description="Cover image"),
            openapi.Parameter('event_date', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="Event date (YYYY-MM-DD)"),
            openapi.Parameter('is_active', openapi.IN_FORM, type=openapi.TYPE_BOOLEAN, required=False),
            openapi.Parameter('sort_order', openapi.IN_FORM, type=openapi.TYPE_INTEGER, required=False),
        ],
        consumes=['multipart/form-data'],
        responses={200: GalleryAlbumDetailSerializer},
        tags=["Gallery - Albums"],
    )
    def patch(self, request, *args, **kwargs):
        obj = self.get_object()
        serializer = GalleryAlbumWriteSerializer(obj, data=request.data, partial=True, context={'request': request})
        serializer.is_valid(raise_exception=True)
        obj = serializer.save()
        return Response(GalleryAlbumDetailSerializer(obj, context={'request': request}).data)

    @swagger_auto_schema(
        operation_summary="Delete album",
        operation_description="Admin only. All photos in the album are also deleted.",
        responses={200: openapi.Response(description="Deleted successfully")},
        tags=["Gallery - Albums"],
    )
    def delete(self, request, *args, **kwargs):
        obj = self.get_object()
        title = obj.title_uz or obj.title_ru or ''
        photos_count = obj.photos_count
        obj.delete()
        return Response(
            {
                'slug': self.kwargs['slug'],
                'title': title,
                'photos_deleted': photos_count,
                'detail': "Album and all its photos deleted successfully.",
            },
            status=status.HTTP_200_OK,
        )


# ─────────────────────────────────────────────────────────────────────────────
# GalleryPhoto
# ─────────────────────────────────────────────────────────────────────────────

class GalleryPhotoUploadView(APIView):
    """
    Upload photo to album.
    POST /gallery/albums/{slug}/photos/ — single photo
    """
    permission_classes = [IsAdminOrReadOnly]
    parser_classes = [MultiPartParser, FormParser]

    def _get_album(self, slug):
        return get_object_or_404(GalleryAlbum, slug=slug)

    def _next_sort_order(self, album):
        last = GalleryPhoto.objects.filter(album=album).order_by('-sort_order').first()
        return (last.sort_order + 1) if last else 1

    @swagger_auto_schema(
        operation_summary="Upload photo to album",
        operation_description=(
            "Admin only. Sent via `multipart/form-data`.\n\n"
            "- `image` — required\n"
            "- `thumbnail` — optional (uses image if not provided)\n"
            "- `caption` — optional caption\n"
            "- `sort_order` — optional (auto-assigned)"
        ),
        manual_parameters=[
            openapi.Parameter('image', openapi.IN_FORM, type=openapi.TYPE_FILE, required=True,
                              description="Main image (JPEG, PNG, WEBP)"),
            openapi.Parameter('thumbnail', openapi.IN_FORM, type=openapi.TYPE_FILE, required=False,
                              description="Preview image (optional)"),
            openapi.Parameter('caption', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False,
                              description="Image caption"),
            openapi.Parameter('sort_order', openapi.IN_FORM, type=openapi.TYPE_INTEGER, required=False),
        ],
        consumes=['multipart/form-data'],
        responses={
            201: GalleryPhotoSerializer,
            400: openapi.Response(description="Validation error"),
            404: openapi.Response(description="Album not found"),
        },
        tags=["Gallery - Photos"],
    )
    def post(self, request, slug):
        album = self._get_album(slug)
        serializer = GalleryPhotoUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        # auto sort_order
        if not data.get('sort_order'):
            data['sort_order'] = self._next_sort_order(album)

        photo = GalleryPhoto.objects.create(album=album, **data)
        return Response(
            GalleryPhotoSerializer(photo, context={'request': request}).data,
            status=status.HTTP_201_CREATED,
        )


class GalleryPhotoBulkUploadView(APIView):
    """
    Upload multiple photos to an album at once.
    POST /gallery/albums/{slug}/photos/bulk/
    """
    permission_classes = [IsAdminOrReadOnly]
    parser_classes = [MultiPartParser, FormParser]

    @swagger_auto_schema(
        operation_summary="Upload multiple photos at once",
        operation_description=(
            "Admin only. Sent via `multipart/form-data`.\n\n"
            "- `images` — multiple image files (`images[]` or `images`)\n"
            "- `caption` — common caption for all images (optional)"
        ),
        manual_parameters=[
            openapi.Parameter('images', openapi.IN_FORM, type=openapi.TYPE_FILE, required=True,
                              description="Multiple image files"),
            openapi.Parameter('caption', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False),
        ],
        consumes=['multipart/form-data'],
        responses={
            201: openapi.Response(description="Uploaded photos list"),
            400: openapi.Response(description="Validation error"),
        },
        tags=["Gallery - Photos"],
    )
    def post(self, request, slug):
        album = get_object_or_404(GalleryAlbum, slug=slug)
        images = request.FILES.getlist('images') or request.FILES.getlist('images[]')

        if not images:
            return Response(
                {'detail': "At least one image is required. Fill the 'images' field."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        caption = request.data.get('caption', '')
        last = GalleryPhoto.objects.filter(album=album).order_by('-sort_order').first()
        next_order = (last.sort_order + 1) if last else 1

        created = []
        for i, image_file in enumerate(images):
            photo = GalleryPhoto.objects.create(
                album=album,
                image=image_file,
                caption=caption or None,
                sort_order=next_order + i,
            )
            created.append(photo)

        return Response(
            {
                'uploaded': len(created),
                'photos': GalleryPhotoSerializer(created, many=True, context={'request': request}).data,
            },
            status=status.HTTP_201_CREATED,
        )


class GalleryPhotoDetailView(APIView):
    """
    Single photo — view, edit, delete.
    GET/PATCH/DELETE /gallery/photos/{id}/
    """
    permission_classes = [IsAdminOrReadOnly]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def _get_photo(self, pk):
        return get_object_or_404(GalleryPhoto.objects.select_related('album'), pk=pk)

    @swagger_auto_schema(
        operation_summary="Photo detail",
        responses={200: GalleryPhotoSerializer, 404: openapi.Response(description="Not found")},
        tags=["Gallery - Photos"],
    )
    def get(self, request, pk):
        photo = self._get_photo(pk)
        return Response(GalleryPhotoSerializer(photo, context={'request': request}).data)

    @swagger_auto_schema(
        operation_summary="Update photo partially",
        operation_description="Update caption and sort_order. Can also replace image file.",
        manual_parameters=[
            openapi.Parameter('image', openapi.IN_FORM, type=openapi.TYPE_FILE, required=False),
            openapi.Parameter('thumbnail', openapi.IN_FORM, type=openapi.TYPE_FILE, required=False),
            openapi.Parameter('caption', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False),
            openapi.Parameter('sort_order', openapi.IN_FORM, type=openapi.TYPE_INTEGER, required=False),
        ],
        consumes=['multipart/form-data'],
        responses={200: GalleryPhotoSerializer},
        tags=["Gallery - Photos"],
    )
    def patch(self, request, pk):
        photo = self._get_photo(pk)
        if 'image' in request.FILES:
            photo.image = request.FILES['image']
        if 'thumbnail' in request.FILES:
            photo.thumbnail = request.FILES['thumbnail']
        if 'caption' in request.data:
            photo.caption = request.data.get('caption') or None
        if 'sort_order' in request.data:
            try:
                photo.sort_order = int(request.data['sort_order'])
            except (ValueError, TypeError):
                return Response({'sort_order': 'Must be an integer.'}, status=status.HTTP_400_BAD_REQUEST)
        photo.save()
        return Response(GalleryPhotoSerializer(photo, context={'request': request}).data)

    @swagger_auto_schema(
        operation_summary="Delete photo",
        operation_description="Admin only. Album's photos_count is updated automatically.",
        responses={200: openapi.Response(description="Deleted successfully")},
        tags=["Gallery - Photos"],
    )
    def delete(self, request, pk):
        photo = self._get_photo(pk)
        album_slug = photo.album.slug
        photo.delete()  # model.delete() automatically updates photos_count
        return Response(
            {'id': pk, 'album_slug': album_slug, 'detail': "Photo deleted successfully."},
            status=status.HTTP_200_OK,
        )


# ─────────────────────────────────────────────────────────────────────────────
# UsefulLink
# ─────────────────────────────────────────────────────────────────────────────

class UsefulLinkListView(generics.ListCreateAPIView):
    """Useful links list and create."""
    permission_classes = [IsAdminOrReadOnly]
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_active']
    search_fields = ['name', 'description']
    ordering_fields = ['sort_order', 'name', 'created_at']
    ordering = ['sort_order', 'name']

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return UsefulLink.objects.none()
        qs = UsefulLink.objects.all()
        is_admin = (
            self.request.user.is_authenticated
            and hasattr(self.request.user, 'is_admin_role')
            and self.request.user.is_admin_role()
        )
        if not is_admin:
            qs = qs.filter(is_active=True)
        return qs

    def get_serializer_class(self):
        if getattr(self, 'swagger_fake_view', False):
            return UsefulLinkSerializer
        return UsefulLinkWriteSerializer if self.request.method == 'POST' else UsefulLinkSerializer

    @swagger_auto_schema(
        operation_summary="Useful links list",
        operation_description=(
            "All useful links.\n\n"
            "- `?is_active=true|false` (for admin)\n"
            "- `?search=...` — search by name"
        ),
        responses={200: UsefulLinkSerializer(many=True)},
        tags=["Gallery - Useful Links"],
    )
    def get(self, request, *args, **kwargs):
        qs = self.filter_queryset(self.get_queryset())
        data = UsefulLinkSerializer(qs, many=True, context={'request': request}).data
        return Response(data)

    @swagger_auto_schema(
        operation_summary="Create new useful link",
        operation_description="Admin only. Use **`multipart/form-data`** for logo upload.",
        manual_parameters=[
            openapi.Parameter('name', openapi.IN_FORM, type=openapi.TYPE_STRING, required=True, description="Link name"),
            openapi.Parameter('url', openapi.IN_FORM, type=openapi.TYPE_STRING, required=True, description="URL address (https://...)"),
            openapi.Parameter('logo', openapi.IN_FORM, type=openapi.TYPE_FILE, required=False, description="Logo image"),
            openapi.Parameter('description', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="Short description"),
            openapi.Parameter('sort_order', openapi.IN_FORM, type=openapi.TYPE_INTEGER, required=False, default=0),
            openapi.Parameter('is_active', openapi.IN_FORM, type=openapi.TYPE_BOOLEAN, required=False, default=True),
        ],
        consumes=['multipart/form-data'],
        responses={
            201: UsefulLinkSerializer,
            400: openapi.Response(description="Validation error"),
        },
        tags=["Gallery - Useful Links"],
    )
    def post(self, request, *args, **kwargs):
        serializer = UsefulLinkWriteSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        link = serializer.save()
        return Response(
            UsefulLinkSerializer(link, context={'request': request}).data,
            status=status.HTTP_201_CREATED,
        )


class UsefulLinkDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Single useful link — view, edit, delete."""
    permission_classes = [IsAdminOrReadOnly]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return UsefulLink.objects.none()
        return UsefulLink.objects.all()

    def get_serializer_class(self):
        if getattr(self, 'swagger_fake_view', False):
            return UsefulLinkSerializer
        if self.request.method in ('PUT', 'PATCH'):
            return UsefulLinkWriteSerializer
        return UsefulLinkSerializer

    @swagger_auto_schema(
        operation_summary="Useful link detail",
        responses={200: UsefulLinkSerializer, 404: openapi.Response(description="Not found")},
        tags=["Gallery - Useful Links"],
    )
    def get(self, request, *args, **kwargs):
        obj = self.get_object()
        return Response(UsefulLinkSerializer(obj, context={'request': request}).data)

    @swagger_auto_schema(
        operation_summary="Update useful link completely",
        operation_description="Admin only. Sent via **`multipart/form-data`**.",
        manual_parameters=[
            openapi.Parameter('name', openapi.IN_FORM, type=openapi.TYPE_STRING, required=True, description="Link name"),
            openapi.Parameter('url', openapi.IN_FORM, type=openapi.TYPE_STRING, required=True, description="URL address (https://...)"),
            openapi.Parameter('logo', openapi.IN_FORM, type=openapi.TYPE_FILE, required=False, description="Logo image"),
            openapi.Parameter('description', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="Short description"),
            openapi.Parameter('sort_order', openapi.IN_FORM, type=openapi.TYPE_INTEGER, required=False, default=0),
            openapi.Parameter('is_active', openapi.IN_FORM, type=openapi.TYPE_BOOLEAN, required=False, default=True),
        ],
        consumes=['multipart/form-data'],
        responses={200: UsefulLinkSerializer},
        tags=["Gallery - Useful Links"],
    )
    def put(self, request, *args, **kwargs):
        obj = self.get_object()
        serializer = UsefulLinkWriteSerializer(obj, data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        obj = serializer.save()
        return Response(UsefulLinkSerializer(obj, context={'request': request}).data)

    @swagger_auto_schema(
        operation_summary="Update useful link partially",
        operation_description="Admin only. Only modified fields. **`multipart/form-data`**.",
        manual_parameters=[
            openapi.Parameter('name', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="Link name"),
            openapi.Parameter('url', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="URL address"),
            openapi.Parameter('logo', openapi.IN_FORM, type=openapi.TYPE_FILE, required=False, description="Logo image"),
            openapi.Parameter('description', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False),
            openapi.Parameter('sort_order', openapi.IN_FORM, type=openapi.TYPE_INTEGER, required=False),
            openapi.Parameter('is_active', openapi.IN_FORM, type=openapi.TYPE_BOOLEAN, required=False),
        ],
        consumes=['multipart/form-data'],
        responses={200: UsefulLinkSerializer},
        tags=["Gallery - Useful Links"],
    )
    def patch(self, request, *args, **kwargs):
        obj = self.get_object()
        serializer = UsefulLinkWriteSerializer(obj, data=request.data, partial=True, context={'request': request})
        serializer.is_valid(raise_exception=True)
        obj = serializer.save()
        return Response(UsefulLinkSerializer(obj, context={'request': request}).data)

    @swagger_auto_schema(
        operation_summary="Delete useful link",
        responses={200: openapi.Response(description="Deleted successfully")},
        tags=["Gallery - Useful Links"],
    )
    def delete(self, request, *args, **kwargs):
        obj = self.get_object()
        data = {'id': obj.pk, 'name': obj.name, 'detail': "Link deleted successfully."}
        obj.delete()
        return Response(data, status=status.HTTP_200_OK)


# ─────────────────────────────────────────────────────────────────────────────
# InfrastructureItem — Lyceum's material and technical resources
# ─────────────────────────────────────────────────────────────────────────────

INFRA_WRITE_PARAMS = [
    openapi.Parameter('title_uz',       openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="Name (UZ)"),
    openapi.Parameter('title_ru',       openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="Name (RU)"),
    openapi.Parameter('description_uz',      openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="Description (UZ)"),
    openapi.Parameter('description_ru',      openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="Description (RU)"),
    openapi.Parameter('image',      openapi.IN_FORM, type=openapi.TYPE_FILE,    required=False, description="Image"),
    openapi.Parameter('sort_order', openapi.IN_FORM, type=openapi.TYPE_INTEGER, required=False, default=0),
    openapi.Parameter('is_active',  openapi.IN_FORM, type=openapi.TYPE_BOOLEAN, required=False, default=True),
]


class InfrastructureListCreateView(generics.ListCreateAPIView):
    """Infrastructure items list and create."""
    permission_classes = [IsAdminOrReadOnly]
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    pagination_class = GalleryPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_active']
    search_fields = ['title_uz', 'title_ru', 'description_uz', 'description_ru']
    ordering_fields = ['sort_order', 'created_at']
    ordering = ['sort_order', '-created_at']

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return InfrastructureItem.objects.none()
        qs = InfrastructureItem.objects.all()
        is_admin = (
            self.request.user.is_authenticated
            and hasattr(self.request.user, 'is_admin_role')
            and self.request.user.is_admin_role()
        )
        if not is_admin:
            qs = qs.filter(is_active=True)
        return qs

    def get_serializer_class(self):
        if getattr(self, 'swagger_fake_view', False):
            return InfrastructureItemSerializer
        return InfrastructureItemWriteSerializer if self.request.method == 'POST' else InfrastructureItemSerializer

    @swagger_auto_schema(
        operation_summary="Infrastructure list",
        operation_description=(
            "Lyceum's infrastructure items (desks, computers, etc.).\n\n"
            "Filters:\n"
            "- `?is_active=true|false` (for admin)\n"
            "- `?search=...` — search by name/description\n"
            "- `?ordering=sort_order|-created_at`\n"
            "- `?lang=uz|ru` — show only that language translation"
        ),
        manual_parameters=[LANG_PARAM],
        responses={200: InfrastructureItemSerializer(many=True)},
        tags=["Infrastructure"],
    )
    def get(self, request, *args, **kwargs):
        lang = request.query_params.get('lang')
        qs = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(qs)
        if page is not None:
            data = InfrastructureItemSerializer(page, many=True, context={'request': request}).data
            return self.get_paginated_response(apply_lang_filter(list(data), lang))
        data = InfrastructureItemSerializer(qs, many=True, context={'request': request}).data
        return Response(apply_lang_filter(list(data), lang))

    @swagger_auto_schema(
        operation_summary="Create new item",
        operation_description=(
            "Admin only. Sent via **`multipart/form-data`**.\n\n"
            "At least one language `title_*` and `image` are required."
        ),
        manual_parameters=INFRA_WRITE_PARAMS,
        consumes=['multipart/form-data'],
        responses={
            201: InfrastructureItemSerializer,
            400: openapi.Response(description="Validation error"),
            403: openapi.Response(description="Permission denied"),
        },
        tags=["Infrastructure"],
    )
    def post(self, request, *args, **kwargs):
        serializer = InfrastructureItemWriteSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        item = serializer.save()
        return Response(
            InfrastructureItemSerializer(item, context={'request': request}).data,
            status=status.HTTP_201_CREATED,
        )


class InfrastructureDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Single item — view, edit, delete."""
    permission_classes = [IsAdminOrReadOnly]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return InfrastructureItem.objects.none()
        return InfrastructureItem.objects.all()

    def get_serializer_class(self):
        if getattr(self, 'swagger_fake_view', False):
            return InfrastructureItemSerializer
        if self.request.method in ('PUT', 'PATCH'):
            return InfrastructureItemWriteSerializer
        return InfrastructureItemSerializer

    @swagger_auto_schema(
        operation_summary="Item detail",
        operation_description="Single infrastructure item. Use ?lang= for language filter.",
        manual_parameters=[LANG_PARAM],
        responses={200: InfrastructureItemSerializer, 404: openapi.Response(description="Not found")},
        tags=["Infrastructure"],
    )
    def get(self, request, *args, **kwargs):
        obj = self.get_object()
        lang = request.query_params.get('lang')
        data = InfrastructureItemSerializer(obj, context={'request': request}).data
        return Response(apply_lang_filter(data, lang))

    @swagger_auto_schema(
        operation_summary="Update item completely",
        operation_description="Admin only. Sent via **`multipart/form-data`**.",
        manual_parameters=INFRA_WRITE_PARAMS,
        consumes=['multipart/form-data'],
        responses={200: InfrastructureItemSerializer, 400: openapi.Response(description="Validation error")},
        tags=["Infrastructure"],
    )
    def put(self, request, *args, **kwargs):
        obj = self.get_object()
        serializer = InfrastructureItemWriteSerializer(obj, data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        obj = serializer.save()
        return Response(InfrastructureItemSerializer(obj, context={'request': request}).data)

    @swagger_auto_schema(
        operation_summary="Update item partially",
        operation_description="Admin only. Only modified fields. **`multipart/form-data`**.",
        manual_parameters=INFRA_WRITE_PARAMS,
        consumes=['multipart/form-data'],
        responses={200: InfrastructureItemSerializer, 400: openapi.Response(description="Validation error")},
        tags=["Infrastructure"],
    )
    def patch(self, request, *args, **kwargs):
        obj = self.get_object()
        serializer = InfrastructureItemWriteSerializer(obj, data=request.data, partial=True, context={'request': request})
        serializer.is_valid(raise_exception=True)
        obj = serializer.save()
        return Response(InfrastructureItemSerializer(obj, context={'request': request}).data)

    @swagger_auto_schema(
        operation_summary="Delete item",
        responses={200: openapi.Response(description="Deleted successfully")},
        tags=["Infrastructure"],
    )
    def delete(self, request, *args, **kwargs):
        obj = self.get_object()
        data = {
            'id': obj.pk,
            'title': obj.title_uz or obj.title_ru or '',
            'detail': "Item deleted successfully.",
        }
        obj.delete()
        return Response(data, status=status.HTTP_200_OK)


# ─────────────────────────────────────────────────────────────────────────────
# Video — Video clips
# ─────────────────────────────────────────────────────────────────────────────

VIDEO_WRITE_PARAMS = [
    openapi.Parameter('title_uz',       openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="Title (UZ)"),
    openapi.Parameter('title_ru',       openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="Title (RU)"),
    openapi.Parameter('description_uz',      openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="Description (UZ)"),
    openapi.Parameter('description_ru',      openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="Description (RU)"),
    openapi.Parameter('video_file', openapi.IN_FORM, type=openapi.TYPE_FILE,    required=True,  description="Video file (mp4, webm, avi, etc.)"),
    openapi.Parameter('thumbnail',  openapi.IN_FORM, type=openapi.TYPE_FILE,    required=False, description="Cover image (optional)"),
    openapi.Parameter('sort_order', openapi.IN_FORM, type=openapi.TYPE_INTEGER, required=False, default=0),
    openapi.Parameter('is_active',  openapi.IN_FORM, type=openapi.TYPE_BOOLEAN, required=False, default=True),
]


class VideoListCreateView(generics.ListCreateAPIView):
    """Video clips list and create."""
    permission_classes = [IsAdminOrReadOnly]
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    pagination_class = GalleryPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_active']
    search_fields = ['title_uz', 'title_ru', 'description_uz', 'description_ru']
    ordering_fields = ['sort_order', 'created_at']
    ordering = ['sort_order', '-created_at']

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Video.objects.none()
        qs = Video.objects.all()
        is_admin = (
            self.request.user.is_authenticated
            and hasattr(self.request.user, 'is_admin_role')
            and self.request.user.is_admin_role()
        )
        if not is_admin:
            qs = qs.filter(is_active=True)
        return qs

    def get_serializer_class(self):
        if getattr(self, 'swagger_fake_view', False):
            return VideoSerializer
        return VideoWriteSerializer if self.request.method == 'POST' else VideoSerializer

    @swagger_auto_schema(
        operation_summary="Video list",
        operation_description=(
            "All video clips.\n\n"
            "Filters:\n"
            "- `?is_active=true|false` (for admin)\n"
            "- `?search=...` — search by title/description\n"
            "- `?ordering=sort_order|-created_at`\n"
            "- `?lang=uz|ru` — show only that language translation"
        ),
        manual_parameters=[LANG_PARAM],
        responses={200: VideoSerializer(many=True)},
        tags=["Gallery - Videos"],
    )
    def get(self, request, *args, **kwargs):
        lang = request.query_params.get('lang')
        qs = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(qs)
        if page is not None:
            data = VideoSerializer(page, many=True, context={'request': request}).data
            return self.get_paginated_response(apply_lang_filter(list(data), lang))
        data = VideoSerializer(qs, many=True, context={'request': request}).data
        return Response(apply_lang_filter(list(data), lang))

    @swagger_auto_schema(
        operation_summary="Create new video",
        operation_description=(
            "Admin only. Sent via **`multipart/form-data`**.\n\n"
            "At least one language `title_*` and `video_url` are required."
        ),
        manual_parameters=VIDEO_WRITE_PARAMS,
        consumes=['multipart/form-data'],
        responses={
            201: VideoSerializer,
            400: openapi.Response(description="Validation error"),
            403: openapi.Response(description="Permission denied"),
        },
        tags=["Gallery - Videos"],
    )
    def post(self, request, *args, **kwargs):
        serializer = VideoWriteSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        video = serializer.save()
        return Response(
            VideoSerializer(video, context={'request': request}).data,
            status=status.HTTP_201_CREATED,
        )


class VideoDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Single video — view, edit, delete."""
    permission_classes = [IsAdminOrReadOnly]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Video.objects.none()
        return Video.objects.all()

    def get_serializer_class(self):
        if getattr(self, 'swagger_fake_view', False):
            return VideoSerializer
        if self.request.method in ('PUT', 'PATCH'):
            return VideoWriteSerializer
        return VideoSerializer

    @swagger_auto_schema(
        operation_summary="Video detail",
        operation_description="Single video clip. Use ?lang= for language filter.",
        manual_parameters=[LANG_PARAM],
        responses={200: VideoSerializer, 404: openapi.Response(description="Not found")},
        tags=["Gallery - Videos"],
    )
    def get(self, request, *args, **kwargs):
        obj = self.get_object()
        lang = request.query_params.get('lang')
        data = VideoSerializer(obj, context={'request': request}).data
        return Response(apply_lang_filter(data, lang))

    @swagger_auto_schema(
        operation_summary="Update video completely",
        operation_description="Admin only. Sent via **`multipart/form-data`**.",
        manual_parameters=VIDEO_WRITE_PARAMS,
        consumes=['multipart/form-data'],
        responses={200: VideoSerializer, 400: openapi.Response(description="Validation error")},
        tags=["Gallery - Videos"],
    )
    def put(self, request, *args, **kwargs):
        obj = self.get_object()
        serializer = VideoWriteSerializer(obj, data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        obj = serializer.save()
        return Response(VideoSerializer(obj, context={'request': request}).data)

    @swagger_auto_schema(
        operation_summary="Update video partially",
        operation_description="Admin only. Only modified fields. **`multipart/form-data`**.",
        manual_parameters=VIDEO_WRITE_PARAMS,
        consumes=['multipart/form-data'],
        responses={200: VideoSerializer, 400: openapi.Response(description="Validation error")},
        tags=["Gallery - Videos"],
    )
    def patch(self, request, *args, **kwargs):
        obj = self.get_object()
        serializer = VideoWriteSerializer(obj, data=request.data, partial=True, context={'request': request})
        serializer.is_valid(raise_exception=True)
        obj = serializer.save()
        return Response(VideoSerializer(obj, context={'request': request}).data)

    @swagger_auto_schema(
        operation_summary="Delete video",
        responses={200: openapi.Response(description="Deleted successfully")},
        tags=["Gallery - Videos"],
    )
    def delete(self, request, *args, **kwargs):
        obj = self.get_object()
        data = {
            'id': obj.pk,
            'title': obj.title_uz or obj.title_ru or '',
            'detail': "Video deleted successfully.",
        }
        obj.delete()
        return Response(data, status=status.HTTP_200_OK)