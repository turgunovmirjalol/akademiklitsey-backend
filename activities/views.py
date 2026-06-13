from rest_framework import generics, filters, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.pagination import PageNumberPagination
from rest_framework.exceptions import NotFound
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from accounts.permissions import IsAdminOrReadOnly
from .models import Circle
from .serializers import CircleSerializer, CircleWriteSerializer

# ─── Swagger parameters ─────────────────────────────────────────────────────

LANG_PARAM = openapi.Parameter(
    'lang', openapi.IN_QUERY,
    description="Filter response language: uz | ru",
    type=openapi.TYPE_STRING,
    enum=['uz', 'ru'],
    required=False,
)

ALL_PARAM = openapi.Parameter(
    'all', openapi.IN_QUERY,
    description="true — all circles (for admin, including inactive)",
    type=openapi.TYPE_BOOLEAN,
    required=False,
)


def apply_lang_filter(data, lang):
    if not lang or lang not in ('uz', 'ru'):
        return data

    def _filter(item):
        if isinstance(item, dict) and 'translations' in item:
            t = item.get('translations') or {}
            chosen = t.get(lang, {})
            if not any(chosen.values()):
                chosen = t.get('uz', {})
            item = dict(item)
            item['translations'] = {lang: chosen}
        return item

    if isinstance(data, list):
        return [_filter(i) for i in data]
    return _filter(data)


# ─── Pagination ──────────────────────────────────────────────────────────────

class CirclePagination(PageNumberPagination):
    page_size = 12
    page_size_query_param = 'page_size'
    max_page_size = 100


# ─── Views ───────────────────────────────────────────────────────────────────

class CircleListView(generics.ListCreateAPIView):
    permission_classes = [IsAdminOrReadOnly]
    pagination_class = CirclePagination
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'is_active']
    search_fields = ['name_uz', 'name_ru', 'description_uz', 'description_ru']
    ordering_fields = ['sort_order', 'current_students', 'name_uz']
    ordering = ['sort_order']

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Circle.objects.none()
        qs = Circle.objects.select_related('teacher').all()
        show_all = self.request.query_params.get('all', '').lower() == 'true'
        is_admin = self.request.user.is_authenticated and hasattr(self.request.user, 'is_admin_role') and self.request.user.is_admin_role()
        if not (show_all and is_admin):
            qs = qs.filter(is_active=True)
        return qs

    def get_serializer_class(self):
        if getattr(self, 'swagger_fake_view', False):
            return CircleSerializer
        return CircleWriteSerializer if self.request.method == 'POST' else CircleSerializer

    @swagger_auto_schema(
        operation_summary="Circles list",
        operation_description=(
            "Active circles list.\n\n"
            "Filters:\n"
            "- `?category=sport|art|science|language|tech|other`\n"
            "- `?is_active=true|false` (admin only)\n"
            "- `?all=true` — include inactive (admin only)\n"
            "- `?search=...` — search by name/description\n"
            "- `?lang=uz|ru` — show only that language translation"
        ),
        manual_parameters=[LANG_PARAM, ALL_PARAM],
        responses={200: CircleSerializer(many=True)},
        tags=["Activities - Circles"],
    )
    def get(self, request, *args, **kwargs):
        lang = request.query_params.get('lang')
        qs = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(qs)
        if page is not None:
            data = CircleSerializer(page, many=True, context={'request': request}).data
            return self.get_paginated_response(apply_lang_filter(list(data), lang))
        data = CircleSerializer(qs, many=True, context={'request': request}).data
        return Response(apply_lang_filter(list(data), lang))

    @swagger_auto_schema(
        operation_summary="Create new circle",
        operation_description=(
            "Admin only. Sent via **`multipart/form-data`**.\n\n"
            "Fields for each language are sent separately.\n"
            "At least one language `name_*` must be filled."
        ),
        manual_parameters=[
            openapi.Parameter('name_uz', openapi.IN_FORM, type=openapi.TYPE_STRING, required=True, description="Name (UZ)"),
            openapi.Parameter('name_ru', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="Name (RU)"),
            openapi.Parameter('description_uz', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="Description (UZ)"),
            openapi.Parameter('description_ru', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="Description (RU)"),
            openapi.Parameter('schedule_uz', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="Schedule (UZ)"),
            openapi.Parameter('schedule_ru', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="Schedule (RU)"),
            openapi.Parameter('category', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, enum=['sport','art','science','language','tech','other'], default='other'),
            openapi.Parameter('teacher', openapi.IN_FORM, type=openapi.TYPE_INTEGER, required=False, description="Teacher ID"),
            openapi.Parameter('max_students', openapi.IN_FORM, type=openapi.TYPE_INTEGER, required=False),
            openapi.Parameter('current_students', openapi.IN_FORM, type=openapi.TYPE_INTEGER, required=False, default=0),
            openapi.Parameter('room', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False),
            openapi.Parameter('photo', openapi.IN_FORM, type=openapi.TYPE_FILE, required=False, description="Circle photo"),
            openapi.Parameter('is_active', openapi.IN_FORM, type=openapi.TYPE_BOOLEAN, required=False, default=True),
            openapi.Parameter('sort_order', openapi.IN_FORM, type=openapi.TYPE_INTEGER, required=False, default=0),
        ],
        consumes=['multipart/form-data'],
        responses={
            201: CircleSerializer,
            400: openapi.Response(description="Validation error"),
            403: openapi.Response(description="Permission denied"),
        },
        tags=["Activities - Circles"],
    )
    def post(self, request, *args, **kwargs):
        serializer = CircleWriteSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        circle = serializer.save()
        return Response(
            CircleSerializer(circle, context={'request': request}).data,
            status=status.HTTP_201_CREATED,
        )


class CircleDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAdminOrReadOnly]
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    lookup_field = 'slug'

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Circle.objects.none()
        return Circle.objects.select_related('teacher').all()

    def get_serializer_class(self):
        if getattr(self, 'swagger_fake_view', False):
            return CircleSerializer
        if self.request.method in ('PUT', 'PATCH'):
            return CircleWriteSerializer
        return CircleSerializer

    def get_object(self):
        obj = get_object_or_404(
            Circle.objects.select_related('teacher'),
            slug=self.kwargs['slug'],
        )
        if not obj.is_active:
            is_admin = (
                self.request.user.is_authenticated
                and hasattr(self.request.user, 'is_admin_role')
                and self.request.user.is_admin_role()
            )
            if not is_admin:
                raise NotFound("This circle was not found.")
        self.check_object_permissions(self.request, obj)
        return obj

    @swagger_auto_schema(
        operation_summary="Circle detail",
        operation_description="Single circle details. Use ?lang= for language filter.",
        manual_parameters=[LANG_PARAM],
        responses={200: CircleSerializer, 404: openapi.Response(description="Not found")},
        tags=["Activities - Circles"],
    )
    def get(self, request, *args, **kwargs):
        obj = self.get_object()
        lang = request.query_params.get('lang')
        data = CircleSerializer(obj, context={'request': request}).data
        return Response(apply_lang_filter(data, lang))

    @swagger_auto_schema(
        operation_summary="Update circle completely",
        operation_description="Admin only. Sent via **`multipart/form-data`**.",
        manual_parameters=[
            openapi.Parameter('name_uz', openapi.IN_FORM, type=openapi.TYPE_STRING, required=True, description="Name (UZ)"),
            openapi.Parameter('name_ru', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="Name (RU)"),
            openapi.Parameter('description_uz', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="Description (UZ)"),
            openapi.Parameter('description_ru', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="Description (RU)"),
            openapi.Parameter('schedule_uz', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="Schedule (UZ)"),
            openapi.Parameter('schedule_ru', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="Schedule (RU)"),
            openapi.Parameter('category', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, enum=['sport','art','science','language','tech','other']),
            openapi.Parameter('teacher', openapi.IN_FORM, type=openapi.TYPE_INTEGER, required=False),
            openapi.Parameter('max_students', openapi.IN_FORM, type=openapi.TYPE_INTEGER, required=False),
            openapi.Parameter('current_students', openapi.IN_FORM, type=openapi.TYPE_INTEGER, required=False),
            openapi.Parameter('room', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False),
            openapi.Parameter('photo', openapi.IN_FORM, type=openapi.TYPE_FILE, required=False, description="Photo"),
            openapi.Parameter('is_active', openapi.IN_FORM, type=openapi.TYPE_BOOLEAN, required=False),
            openapi.Parameter('sort_order', openapi.IN_FORM, type=openapi.TYPE_INTEGER, required=False),
        ],
        consumes=['multipart/form-data'],
        responses={200: CircleSerializer, 400: openapi.Response(description="Validation error")},
        tags=["Activities - Circles"],
    )
    def put(self, request, *args, **kwargs):
        obj = self.get_object()
        serializer = CircleWriteSerializer(obj, data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        obj = serializer.save()
        return Response(CircleSerializer(obj, context={'request': request}).data)

    @swagger_auto_schema(
        operation_summary="Update circle partially",
        operation_description="Admin only. Only modified fields. **`multipart/form-data`**.",
        manual_parameters=[
            openapi.Parameter('name_uz', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="Name (UZ)"),
            openapi.Parameter('name_ru', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="Name (RU)"),
            openapi.Parameter('description_uz', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="Description (UZ)"),
            openapi.Parameter('description_ru', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="Description (RU)"),
            openapi.Parameter('schedule_uz', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="Schedule (UZ)"),
            openapi.Parameter('schedule_ru', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="Schedule (RU)"),
            openapi.Parameter('category', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, enum=['sport','art','science','language','tech','other']),
            openapi.Parameter('teacher', openapi.IN_FORM, type=openapi.TYPE_INTEGER, required=False),
            openapi.Parameter('max_students', openapi.IN_FORM, type=openapi.TYPE_INTEGER, required=False),
            openapi.Parameter('current_students', openapi.IN_FORM, type=openapi.TYPE_INTEGER, required=False),
            openapi.Parameter('room', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False),
            openapi.Parameter('photo', openapi.IN_FORM, type=openapi.TYPE_FILE, required=False, description="Photo"),
            openapi.Parameter('is_active', openapi.IN_FORM, type=openapi.TYPE_BOOLEAN, required=False),
            openapi.Parameter('sort_order', openapi.IN_FORM, type=openapi.TYPE_INTEGER, required=False),
        ],
        consumes=['multipart/form-data'],
        responses={200: CircleSerializer, 400: openapi.Response(description="Validation error")},
        tags=["Activities - Circles"],
    )
    def patch(self, request, *args, **kwargs):
        obj = self.get_object()
        serializer = CircleWriteSerializer(obj, data=request.data, partial=True, context={'request': request})
        serializer.is_valid(raise_exception=True)
        obj = serializer.save()
        return Response(CircleSerializer(obj, context={'request': request}).data)

    @swagger_auto_schema(
        operation_summary="Delete circle",
        operation_description="Admin only.",
        responses={200: openapi.Response(description="Deleted successfully")},
        tags=["Activities - Circles"],
    )
    def delete(self, request, *args, **kwargs):
        obj = self.get_object()
        data = {
            'id': obj.id,
            'slug': obj.slug,
            'name': obj.name_uz or obj.name_ru or '',
            'detail': "Circle deleted successfully.",
        }
        obj.delete()
        return Response(data, status=status.HTTP_200_OK)