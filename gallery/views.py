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

# ─── Swagger parametrlar ─────────────────────────────────────────────────────

LANG_PARAM = openapi.Parameter(
    'lang', openapi.IN_QUERY,
    description="Javob tilini filtrlash: uz | ru",
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
    """Album ro'yxati va yaratish."""
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
        # Oddiy foydalanuvchi faqat faol albomlarni ko'radi
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
        operation_summary="Galereya albomlari ro'yxati",
        operation_description=(
            "Barcha galereya albomlari.\n\n"
            "Filterlar:\n"
            "- `?is_active=true|false` (admin uchun)\n"
            "- `?event_date=YYYY-MM-DD`\n"
            "- `?search=...` — nom/tavsif bo'yicha\n"
            "- `?ordering=sort_order|-created_at|photos_count`\n"
            "- `?lang=uz|ru` — faqat o'sha tildagi tarjima"
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
        operation_summary="Yangi album yaratish",
        operation_description=(
            "Faqat admin. **`multipart/form-data`** orqali yuboriladi.\n\n"
            "Har bir til uchun maydonlar alohida yuboriladi.\n"
            "Kamida bitta tilda `title_*` to'ldirilishi shart.\n\n"
            "**Muhim:** Rasm yuklash uchun `Content-Type: multipart/form-data` ishlatiladi.\n"
            "JSON bilan rasm yuklash mumkin emas."
        ),
        manual_parameters=[
            openapi.Parameter('title_uz', openapi.IN_FORM, type=openapi.TYPE_STRING, required=True, description="Album nomi (UZ)"),
            openapi.Parameter('title_ru', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="Album nomi (RU)"),
            openapi.Parameter('description_uz', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="Tavsif (UZ)"),
            openapi.Parameter('description_ru', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="Tavsif (RU)"),
            openapi.Parameter('cover_image', openapi.IN_FORM, type=openapi.TYPE_FILE, required=False, description="Muqova rasmi"),
            openapi.Parameter('event_date', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="Tadbir sanasi (YYYY-MM-DD)"),
            openapi.Parameter('is_active', openapi.IN_FORM, type=openapi.TYPE_BOOLEAN, required=False, default=True),
            openapi.Parameter('sort_order', openapi.IN_FORM, type=openapi.TYPE_INTEGER, required=False, default=0),
        ],
        consumes=['multipart/form-data'],
        responses={
            201: GalleryAlbumDetailSerializer,
            400: openapi.Response(description="Validatsiya xatosi"),
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
    """Bitta album — ko'rish (rasmlar bilan), tahrirlash, o'chirish."""
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
            raise NotFound("Bu albom topilmadi.")
        self.check_object_permissions(self.request, obj)
        return obj

    @swagger_auto_schema(
        operation_summary="Album detali (rasmlar bilan)",
        operation_description="Bitta album va uning barcha rasmlari. ?lang= bilan til filtri.",
        manual_parameters=[LANG_PARAM],
        responses={200: GalleryAlbumDetailSerializer, 404: openapi.Response(description="Topilmadi")},
        tags=["Gallery - Albums"],
    )
    def get(self, request, *args, **kwargs):
        obj = self.get_object()
        lang = request.query_params.get('lang')
        data = GalleryAlbumDetailSerializer(obj, context={'request': request}).data
        return Response(apply_lang_filter(data, lang))

    @swagger_auto_schema(
        operation_summary="Albumni to'liq yangilash",
        operation_description="Faqat admin. **`multipart/form-data`** orqali yuboriladi.",
        manual_parameters=[
            openapi.Parameter('title_uz', openapi.IN_FORM, type=openapi.TYPE_STRING, required=True, description="Album nomi (UZ)"),
            openapi.Parameter('title_ru', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="Album nomi (RU)"),
            openapi.Parameter('description_uz', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="Tavsif (UZ)"),
            openapi.Parameter('description_ru', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="Tavsif (RU)"),
            openapi.Parameter('cover_image', openapi.IN_FORM, type=openapi.TYPE_FILE, required=False, description="Muqova rasmi"),
            openapi.Parameter('event_date', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="Tadbir sanasi (YYYY-MM-DD)"),
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
        operation_summary="Albumni qisman yangilash",
        operation_description="Faqat admin. Faqat o'zgartirilishi kerak bo'lgan maydonlar. **`multipart/form-data`**.",
        manual_parameters=[
            openapi.Parameter('title_uz', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="Album nomi (UZ)"),
            openapi.Parameter('title_ru', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="Album nomi (RU)"),
            openapi.Parameter('description_uz', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="Tavsif (UZ)"),
            openapi.Parameter('description_ru', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="Tavsif (RU)"),
            openapi.Parameter('cover_image', openapi.IN_FORM, type=openapi.TYPE_FILE, required=False, description="Muqova rasmi"),
            openapi.Parameter('event_date', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="Tadbir sanasi (YYYY-MM-DD)"),
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
        operation_summary="Albumni o'chirish",
        operation_description="Faqat admin. Albom bilan birga barcha rasmlar ham o'chiriladi.",
        responses={200: openapi.Response(description="Muvaffaqiyatli o'chirildi")},
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
                'detail': "Album va barcha rasmlari muvaffaqiyatli o'chirildi.",
            },
            status=status.HTTP_200_OK,
        )


# ─────────────────────────────────────────────────────────────────────────────
# GalleryPhoto
# ─────────────────────────────────────────────────────────────────────────────

class GalleryPhotoUploadView(APIView):
    """
    Albomga rasm yuklash.
    POST /gallery/albums/{slug}/photos/ — bitta rasm
    """
    permission_classes = [IsAdminOrReadOnly]
    parser_classes = [MultiPartParser, FormParser]

    def _get_album(self, slug):
        return get_object_or_404(GalleryAlbum, slug=slug)

    def _next_sort_order(self, album):
        last = GalleryPhoto.objects.filter(album=album).order_by('-sort_order').first()
        return (last.sort_order + 1) if last else 1

    @swagger_auto_schema(
        operation_summary="Albomga rasm yuklash",
        operation_description=(
            "Faqat admin. `multipart/form-data` orqali yuboriladi.\n\n"
            "- `image` — majburiy\n"
            "- `thumbnail` — ixtiyoriy (yo'q bo'lsa image ishlatiladi)\n"
            "- `caption` — ixtiyoriy izoh\n"
            "- `sort_order` — ixtiyoriy (avtomatik belgilanadi)"
        ),
        manual_parameters=[
            openapi.Parameter('image', openapi.IN_FORM, type=openapi.TYPE_FILE, required=True, description="Asosiy rasm (JPEG, PNG, WEBP)"),
            openapi.Parameter('thumbnail', openapi.IN_FORM, type=openapi.TYPE_FILE, required=False, description="Preview rasm (ixtiyoriy)"),
            openapi.Parameter('caption', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="Rasm izohi"),
            openapi.Parameter('sort_order', openapi.IN_FORM, type=openapi.TYPE_INTEGER, required=False),
        ],
        consumes=['multipart/form-data'],
        responses={
            201: GalleryPhotoSerializer,
            400: openapi.Response(description="Validatsiya xatosi"),
            404: openapi.Response(description="Album topilmadi"),
        },
        tags=["Gallery - Photos"],
    )
    def post(self, request, slug):
        album = self._get_album(slug)
        serializer = GalleryPhotoUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        # sort_order avtomatik
        if not data.get('sort_order'):
            data['sort_order'] = self._next_sort_order(album)

        photo = GalleryPhoto.objects.create(album=album, **data)
        return Response(
            GalleryPhotoSerializer(photo, context={'request': request}).data,
            status=status.HTTP_201_CREATED,
        )


class GalleryPhotoBulkUploadView(APIView):
    """
    Albomga bir vaqtda bir nechta rasm yuklash.
    POST /gallery/albums/{slug}/photos/bulk/
    """
    permission_classes = [IsAdminOrReadOnly]
    parser_classes = [MultiPartParser, FormParser]

    @swagger_auto_schema(
        operation_summary="Bir vaqtda bir nechta rasm yuklash",
        operation_description=(
            "Faqat admin. `multipart/form-data` orqali yuboriladi.\n\n"
            "- `images` — bir nechta rasm fayllari (`images[]` yoki `images`)\n"
            "- `caption` — barcha rasmlarga umumiy izoh (ixtiyoriy)"
        ),
        manual_parameters=[
            openapi.Parameter('images', openapi.IN_FORM, type=openapi.TYPE_FILE, required=True, description="Bir nechta rasm fayllari"),
            openapi.Parameter('caption', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False),
        ],
        consumes=['multipart/form-data'],
        responses={
            201: openapi.Response(description="Yuklangan rasmlar ro'yxati"),
            400: openapi.Response(description="Validatsiya xatosi"),
        },
        tags=["Gallery - Photos"],
    )
    def post(self, request, slug):
        album = get_object_or_404(GalleryAlbum, slug=slug)
        images = request.FILES.getlist('images') or request.FILES.getlist('images[]')

        if not images:
            return Response(
                {'detail': "Kamida bitta rasm yuklash shart. 'images' maydonini to'ldiring."},
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
    Bitta rasm — ko'rish, tahrirlash, o'chirish.
    GET/PATCH/DELETE /gallery/photos/{id}/
    """
    permission_classes = [IsAdminOrReadOnly]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def _get_photo(self, pk):
        return get_object_or_404(GalleryPhoto.objects.select_related('album'), pk=pk)

    @swagger_auto_schema(
        operation_summary="Rasm detali",
        responses={200: GalleryPhotoSerializer, 404: openapi.Response(description="Topilmadi")},
        tags=["Gallery - Photos"],
    )
    def get(self, request, pk):
        photo = self._get_photo(pk)
        return Response(GalleryPhotoSerializer(photo, context={'request': request}).data)

    @swagger_auto_schema(
        operation_summary="Rasmni qisman yangilash",
        operation_description="caption va sort_order ni yangilash. Rasm faylini almashtirish ham mumkin.",
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
                return Response({'sort_order': 'Butun son bo'lishi kerak.'}, status=status.HTTP_400_BAD_REQUEST)
        photo.save()
        return Response(GalleryPhotoSerializer(photo, context={'request': request}).data)

    @swagger_auto_schema(
        operation_summary="Rasmni o'chirish",
        operation_description="Faqat admin. Albomning photos_count avtomatik yangilanadi.",
        responses={200: openapi.Response(description="Muvaffaqiyatli o'chirildi")},
        tags=["Gallery - Photos"],
    )
    def delete(self, request, pk):
        photo = self._get_photo(pk)
        album_slug = photo.album.slug
        photo.delete()  # model.delete() photos_count ni avtomatik yangilanadi
        return Response(
            {'id': pk, 'album_slug': album_slug, 'detail': "Rasm muvaffaqiyatli o'chirildi."},
            status=status.HTTP_200_OK,
        )


# ─────────────────────────────────────────────────────────────────────────────
# UsefulLink
# ─────────────────────────────────────────────────────────────────────────────

class UsefulLinkListView(generics.ListCreateAPIView):
    """Foydali havolalar ro'yxati va yaratish."""
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
        operation_summary="Foydali havolalar ro'yxati",
        operation_description="Barcha foydali havolalar.\n\n"
        "- `?is_active=true|false` (admin uchun)\n"
        "- `?search=...` — nom bo'yicha qidirish",
        responses={200: UsefulLinkSerializer(many=True)},
        tags=["Gallery - Useful Links"],
    )
    def get(self, request, *args, **kwargs):
        qs = self.filter_queryset(self.get_queryset())
        data = UsefulLinkSerializer(qs, many=True, context={'request': request}).data
        return Response(data)

    @swagger_auto_schema(
        operation_summary="Yangi foydali havola yaratish",
        operation_description="Faqat admin. Logo yuklash uchun **`multipart/form-data`** ishlatiladi.",
        manual_parameters=[
            openapi.Parameter('name', openapi.IN_FORM, type=openapi.TYPE_STRING, required=True, description="Havola nomi"),
            openapi.Parameter('url', openapi.IN_FORM, type=openapi.TYPE_STRING, required=True, description="URL manzil (https://...)"),
            openapi.Parameter('logo', openapi.IN_FORM, type=openapi.TYPE_FILE, required=False, description="Logo rasmi"),
            openapi.Parameter('description', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="Qisqa tavsif"),
            openapi.Parameter('sort_order', openapi.IN_FORM, type=openapi.TYPE_INTEGER, required=False, default=0),
            openapi.Parameter('is_active', openapi.IN_FORM, type=openapi.TYPE_BOOLEAN, required=False, default=True),
        ],
        consumes=['multipart/form-data'],
        responses={
            201: UsefulLinkSerializer,
            400: openapi.Response(description="Validatsiya xatosi"),
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
    """Bitta foydali havola — ko'rish, tahrirlash, o'chirish."""
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
        operation_summary="Foydali havola detali",
        responses={200: UsefulLinkSerializer, 404: openapi.Response(description="Topilmadi")},
        tags=["Gallery - Useful Links"],
    )
    def get(self, request, *args, **kwargs):
        obj = self.get_object()
        return Response(UsefulLinkSerializer(obj, context={'request': request}).data)

    @swagger_auto_schema(
        operation_summary="Foydali havolani to'liq yangilash",
        operation_description="Faqat admin. **`multipart/form-data`** orqali yuboriladi.",
        manual_parameters=[
            openapi.Parameter('name', openapi.IN_FORM, type=openapi.TYPE_STRING, required=True, description="Havola nomi"),
            openapi.Parameter('url', openapi.IN_FORM, type=openapi.TYPE_STRING, required=True, description="URL manzil (https://...)"),
            openapi.Parameter('logo', openapi.IN_FORM, type=openapi.TYPE_FILE, required=False, description="Logo rasmi"),
            openapi.Parameter('description', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="Qisqa tavsif"),
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
        operation_summary="Foydali havolani qisman yangilash",
        operation_description="Faqat admin. Faqat o'zgartirilishi kerak bo'lgan maydonlar. **`multipart/form-data`**.",
        manual_parameters=[
            openapi.Parameter('name', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="Havola nomi"),
            openapi.Parameter('url', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="URL manzil"),
            openapi.Parameter('logo', openapi.IN_FORM, type=openapi.TYPE_FILE, required=False, description="Logo rasmi"),
            openapi.Parameter('description', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="Qisqa tavsif"),
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
        operation_summary="Foydali havolani o'chirish",
        responses={200: openapi.Response(description="Muvaffaqiyatli o'chirildi")},
        tags=["Gallery - Useful Links"],
    )
    def delete(self, request, *args, **kwargs):
        obj = self.get_object()
        data = {'id': obj.pk, 'name': obj.name, 'detail': "Havola muvaffaqiyatli o'chirildi."}
        obj.delete()
        return Response(data, status=status.HTTP_200_OK)


# ─────────────────────────────────────────────────────────────────────────────
# InfrastructureItem — Litseyning moddiy-texnik bazasi
# ─────────────────────────────────────────────────────────────────────────────

INFRA_WRITE_PARAMS = [
    openapi.Parameter('title_uz', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="Nomi (UZ)"),
    openapi.Parameter('title_ru', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="Nomi (RU)"),
    openapi.Parameter('description_uz', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="Tavsif (UZ)"),
    openapi.Parameter('description_ru', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="Tavsif (RU)"),
    openapi.Parameter('image', openapi.IN_FORM, type=openapi.TYPE_FILE, required=False, description="Rasm"),
    openapi.Parameter('sort_order', openapi.IN_FORM, type=openapi.TYPE_INTEGER, required=False, default=0),
    openapi.Parameter('is_active', openapi.IN_FORM, type=openapi.TYPE_BOOLEAN, required=False, default=True),
]


class InfrastructureListCreateView(generics.ListCreateAPIView):
    """Moddiy-texnik baza elementlari ro'yxati va yaratish."""
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
        operation_summary="Moddiy-texnik baza ro'yxati",
        operation_description=(
            "Litseyning moddiy-texnik bazasi elementlari (partalari, kompyuterlari va boshqalari).\n\n"
            "Filterlar:\n"
            "- `?is_active=true|false` (admin uchun)\n"
            "- `?search=...` — nom/tavsif bo'yicha\n"
            "- `?ordering=sort_order|-created_at`\n"
            "- `?lang=uz|ru` — faqat o'sha tildagi tarjima"
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
        operation_summary="Yangi element yaratish",
        operation_description=(
            "Faqat admin. **`multipart/form-data`** orqali yuboriladi.\n\n"
            "Kamida bitta tilda `title_*` va `image` majburiy."
        ),
        manual_parameters=INFRA_WRITE_PARAMS,
        consumes=['multipart/form-data'],
        responses={
            201: InfrastructureItemSerializer,
            400: openapi.Response(description="Validatsiya xatosi"),
            403: openapi.Response(description="Ruxsat yo'q"),
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
    """Bitta element — ko'rish, tahrirlash, o'chirish."""
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
        operation_summary="Element detali",
        operation_description="Bitta moddiy-texnik baza elementi. ?lang= bilan til filtri.",
        manual_parameters=[LANG_PARAM],
        responses={200: InfrastructureItemSerializer, 404: openapi.Response(description="Topilmadi")},
        tags=["Infrastructure"],
    )
    def get(self, request, *args, **kwargs):
        obj = self.get_object()
        lang = request.query_params.get('lang')
        data = InfrastructureItemSerializer(obj, context={'request': request}).data
        return Response(apply_lang_filter(data, lang))

    @swagger_auto_schema(
        operation_summary="Elementni to'liq yangilash",
        operation_description="Faqat admin. **`multipart/form-data`** orqali yuboriladi.",
        manual_parameters=INFRA_WRITE_PARAMS,
        consumes=['multipart/form-data'],
        responses={200: InfrastructureItemSerializer, 400: openapi.Response(description="Validatsiya xatosi")},
        tags=["Infrastructure"],
    )
    def put(self, request, *args, **kwargs):
        obj = self.get_object()
        serializer = InfrastructureItemWriteSerializer(obj, data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        obj = serializer.save()
        return Response(InfrastructureItemSerializer(obj, context={'request': request}).data)

    @swagger_auto_schema(
        operation_summary="Elementni qisman yangilash",
        operation_description="Faqat admin. Faqat o'zgartirilishi kerak bo'lgan maydonlar. **`multipart/form-data`**.",
        manual_parameters=INFRA_WRITE_PARAMS,
        consumes=['multipart/form-data'],
        responses={200: InfrastructureItemSerializer, 400: openapi.Response(description="Validatsiya xatosi")},
        tags=["Infrastructure"],
    )
    def patch(self, request, *args, **kwargs):
        obj = self.get_object()
        serializer = InfrastructureItemWriteSerializer(obj, data=request.data, partial=True, context={'request': request})
        serializer.is_valid(raise_exception=True)
        obj = serializer.save()
        return Response(InfrastructureItemSerializer(obj, context={'request': request}).data)

    @swagger_auto_schema(
        operation_summary="Elementni o'chirish",
        responses={200: openapi.Response(description="Muvaffaqiyatli o'chirildi")},
        tags=["Infrastructure"],
    )
    def delete(self, request, *args, **kwargs):
        obj = self.get_object()
        data = {
            'id': obj.pk,
            'title': obj.title_uz or obj.title_ru or '',
            'detail': "Element muvaffaqiyatli o'chirildi.",
        }
        obj.delete()
        return Response(data, status=status.HTTP_200_OK)


# ─────────────────────────────────────────────────────────────────────────────
# Video — Video lavhalar
# ─────────────────────────────────────────────────────────────────────────────

VIDEO_WRITE_PARAMS = [
    openapi.Parameter('title_uz', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="Sarlavha (UZ)"),
    openapi.Parameter('title_ru', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="Sarlavha (RU)"),
    openapi.Parameter('description_uz', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="Tavsif (UZ)"),
    openapi.Parameter('description_ru', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="Tavsif (RU)"),
    openapi.Parameter('video_url', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="Video URL"),
    openapi.Parameter('video_file', openapi.IN_FORM, type=openapi.TYPE_FILE, required=False, description="Video fayl"),
    openapi.Parameter('thumbnail', openapi.IN_FORM, type=openapi.TYPE_FILE, required=False, description="Thumbnail rasmi"),
    openapi.Parameter('sort_order', openapi.IN_FORM, type=openapi.TYPE_INTEGER, required=False, default=0),
    openapi.Parameter('is_active', openapi.IN_FORM, type=openapi.TYPE_BOOLEAN, required=False, default=True),
]


class VideoListView(generics.ListCreateAPIView):
    """Video lavhalar ro'yxati va yaratish."""
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
        operation_summary="Video lavhalar ro'yxati",
        operation_description=(
            "Barcha video lavhalar.\n\n"
            "Filterlar:\n"
            "- `?is_active=true|false` (admin uchun)\n"
            "- `?search=...` — nom/tavsif bo'yicha\n"
            "- `?ordering=sort_order|-created_at`\n"
            "- `?lang=uz|ru` — faqat o'sha tildagi tarjima"
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
        operation_summary="Yangi video yaratish",
        operation_description=(
            "Faqat admin. **`multipart/form-data`** orqali yuboriladi.\n\n"
            "Kamida bitta tilda `title_*` to'ldirilishi shart.\n\n"
            "Video uchun `video_url` yoki `video_file` orqali yuklanishi kerak."
        ),
        manual_parameters=VIDEO_WRITE_PARAMS,
        consumes=['multipart/form-data'],
        responses={
            201: VideoSerializer,
            400: openapi.Response(description="Validatsiya xatosi"),
            403: openapi.Response(description="Ruxsat yo'q"),
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
    """Bitta video — ko'rish, tahrirlash, o'chirish."""
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
        operation_summary="Video detali",
        operation_description="Bitta video lavha. ?lang= bilan til filtri.",
        manual_parameters=[LANG_PARAM],
        responses={200: VideoSerializer, 404: openapi.Response(description="Topilmadi")},
        tags=["Gallery - Videos"],
    )
    def get(self, request, *args, **kwargs):
        obj = self.get_object()
        lang = request.query_params.get('lang')
        data = VideoSerializer(obj, context={'request': request}).data
        return Response(apply_lang_filter(data, lang))

    @swagger_auto_schema(
        operation_summary="Videoni to'liq yangilash",
        operation_description="Faqat admin. **`multipart/form-data`** orqali yuboriladi.",
        manual_parameters=VIDEO_WRITE_PARAMS,
        consumes=['multipart/form-data'],
        responses={200: VideoSerializer, 400: openapi.Response(description="Validatsiya xatosi")},
        tags=["Gallery - Videos"],
    )
    def put(self, request, *args, **kwargs):
        obj = self.get_object()
        serializer = VideoWriteSerializer(obj, data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        obj = serializer.save()
        return Response(VideoSerializer(obj, context={'request': request}).data)

    @swagger_auto_schema(
        operation_summary="Videoni qisman yangilash",
        operation_description="Faqat admin. Faqat o'zgartirilishi kerak bo'lgan maydonlar. **`multipart/form-data`**.",
        manual_parameters=VIDEO_WRITE_PARAMS,
        consumes=['multipart/form-data'],
        responses={200: VideoSerializer, 400: openapi.Response(description="Validatsiya xatosi")},
        tags=["Gallery - Videos"],
    )
    def patch(self, request, *args, **kwargs):
        obj = self.get_object()
        serializer = VideoWriteSerializer(obj, data=request.data, partial=True, context={'request': request})
        serializer.is_valid(raise_exception=True)
        obj = serializer.save()
        return Response(VideoSerializer(obj, context={'request': request}).data)

    @swagger_auto_schema(
        operation_summary="Videoni o'chirish",
        responses={200: openapi.Response(description="Muvaffaqiyatli o'chirildi")},
        tags=["Gallery - Videos"],
    )
    def delete(self, request, *args, **kwargs):
        obj = self.get_object()
        data = {
            'id': obj.pk,
            'title': obj.title_uz or obj.title_ru or '',
            'detail': "Video muvaffaqiyatli o'chirildi.",
        }
        obj.delete()
        return Response(data, status=status.HTTP_200_OK)
