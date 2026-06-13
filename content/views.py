from rest_framework import generics, filters, status
from rest_framework.permissions import IsAuthenticatedOrReadOnly, AllowAny
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, F
from django.utils import timezone
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from .models import News, Announcement
from .serializers import (
    NewsSerializer,
    NewsWriteSerializer,
    AnnouncementSerializer,
    AnnouncementWriteSerializer,
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

ACTIVE_ONLY_PARAM = openapi.Parameter(
    'active_only', openapi.IN_QUERY,
    description="true — muddati o'tmagan e'lonlar (faqat Announcement uchun)",
    type=openapi.TYPE_BOOLEAN,
    required=False,
)


# ─── Pagination ──────────────────────────────────────────────────────────────

class ContentPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100


# ─────────────────────────────────────────────────────────────────────────────
# News
# ─────────────────────────────────────────────────────────────────────────────

class NewsListCreateAPIView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticatedOrReadOnly]
    pagination_class = ContentPagination
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'is_featured']
    search_fields = [
        'title_uz', 'title_ru',
        'short_description_uz', 'short_description_ru',
    ]
    ordering_fields = ['created_at', 'published_at', 'views_count']
    ordering = ['-published_at', '-created_at']

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return News.objects.none()
        return News.objects.select_related('created_by').all()

    def get_serializer_class(self):
        if getattr(self, 'swagger_fake_view', False):
            return NewsSerializer
        return NewsWriteSerializer if self.request.method == 'POST' else NewsSerializer

    @swagger_auto_schema(
        operation_summary="Yangiliklar ro'yxati",
        operation_description=(
            "Barcha yangiliklar. Filterlar:\n"
            "- `?status=draft|published|archived`\n"
            "- `?is_featured=true|false`\n"
            "- `?search=...` — sarlavha/tavsif bo'yicha qidirish\n"
            "- `?ordering=published_at|-published_at|views_count`\n"
            "- `?lang=uz|ru` — faqat o'sha tildagi tarjima"
        ),
        manual_parameters=[LANG_PARAM],
        responses={200: NewsSerializer(many=True)},
        tags=['Content - News'],
    )
    def get(self, request, *args, **kwargs):
        lang = request.query_params.get('lang')
        qs = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(qs)
        if page is not None:
            data = NewsSerializer(page, many=True, context={'request': request}).data
            return self.get_paginated_response(apply_lang_filter(list(data), lang))
        data = NewsSerializer(qs, many=True, context={'request': request}).data
        return Response(apply_lang_filter(list(data), lang))

    @swagger_auto_schema(
        operation_summary="Yangi yangilik yaratish",
        operation_description=(
            "Autentifikatsiya talab qilinadi. **`multipart/form-data`** orqali yuboriladi.\n\n"
            "Kamida bitta tilda `title_*` to'ldirilishi shart."
        ),
        manual_parameters=[
            openapi.Parameter('title_uz', openapi.IN_FORM, type=openapi.TYPE_STRING, required=True, description="Sarlavha (UZ)"),
            openapi.Parameter('title_ru', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="Sarlavha (RU)"),
            openapi.Parameter('short_description_uz', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="Qisqa tavsif (UZ)"),
            openapi.Parameter('short_description_ru', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="Qisqa tavsif (RU)"),
            openapi.Parameter('content_uz', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="To'liq matn (UZ)"),
            openapi.Parameter('content_ru', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="To'liq matn (RU)"),
            openapi.Parameter('image', openapi.IN_FORM, type=openapi.TYPE_FILE, required=False, description="Asosiy rasm"),
            openapi.Parameter('status', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, enum=['draft','published','archived'], default='draft'),
            openapi.Parameter('is_featured', openapi.IN_FORM, type=openapi.TYPE_BOOLEAN, required=False, default=False),
            openapi.Parameter('published_at', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="Nashr sanasi (ISO 8601)"),
        ],
        consumes=['multipart/form-data'],
        responses={
            201: NewsSerializer,
            400: openapi.Response(description="Validatsiya xatosi"),
            401: openapi.Response(description="Autentifikatsiya talab qilinadi"),
        },
        tags=['Content - News'],
    )
    def post(self, request, *args, **kwargs):
        serializer = NewsWriteSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        news = serializer.save()
        return Response(
            NewsSerializer(news, context={'request': request}).data,
            status=status.HTTP_201_CREATED,
        )


class NewsDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticatedOrReadOnly]
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    lookup_field = 'slug'

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return News.objects.none()
        return News.objects.select_related('created_by').all()

    def get_serializer_class(self):
        if getattr(self, 'swagger_fake_view', False):
            return NewsSerializer
        if self.request.method in ('PUT', 'PATCH'):
            return NewsWriteSerializer
        return NewsSerializer

    @swagger_auto_schema(
        operation_summary="Yangilik detali",
        operation_description="Bitta yangilik. Ko'rishlar soni avtomatik oshadi. ?lang= bilan til filtri.",
        manual_parameters=[LANG_PARAM],
        responses={200: NewsSerializer, 404: openapi.Response(description="Topilmadi")},
        tags=['Content - News'],
    )
    def get(self, request, *args, **kwargs):
        obj = self.get_object()
        obj.increment_views()
        lang = request.query_params.get('lang')
        data = NewsSerializer(obj, context={'request': request}).data
        return Response(apply_lang_filter(data, lang))

    @swagger_auto_schema(
        operation_summary="Yangilikni to'liq yangilash",
        operation_description="Faqat autentifikatsiyadan o'tgan foydalanuvchi. **`multipart/form-data`** orqali yuboriladi.",
        manual_parameters=[
            openapi.Parameter('title_uz', openapi.IN_FORM, type=openapi.TYPE_STRING, required=True, description="Sarlavha (UZ)"),
            openapi.Parameter('title_ru', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="Sarlavha (RU)"),
            openapi.Parameter('short_description_uz', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="Qisqa tavsif (UZ)"),
            openapi.Parameter('short_description_ru', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="Qisqa tavsif (RU)"),
            openapi.Parameter('content_uz', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="To'liq matn (UZ)"),
            openapi.Parameter('content_ru', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="To'liq matn (RU)"),
            openapi.Parameter('image', openapi.IN_FORM, type=openapi.TYPE_FILE, required=False, description="Asosiy rasm"),
            openapi.Parameter('status', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, enum=['draft', 'published', 'archived'], default='draft'),
            openapi.Parameter('is_featured', openapi.IN_FORM, type=openapi.TYPE_BOOLEAN, required=False, default=False),
            openapi.Parameter('published_at', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="Nashr sanasi (ISO 8601)"),
        ],
        consumes=['multipart/form-data'],
        responses={200: NewsSerializer, 400: openapi.Response(description="Validatsiya xatosi")},
        tags=['Content - News'],
    )
    def put(self, request, *args, **kwargs):
        obj = self.get_object()
        serializer = NewsWriteSerializer(obj, data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        obj = serializer.save()
        return Response(NewsSerializer(obj, context={'request': request}).data)

    @swagger_auto_schema(
        operation_summary="Yangilikni qisman yangilash",
        operation_description="Faqat autentifikatsiyadan o'tgan foydalanuvchi. Faqat o'zgartirilishi kerak bo'lgan maydonlar. **`multipart/form-data`**.",
        manual_parameters=[
            openapi.Parameter('title_uz', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="Sarlavha (UZ)"),
            openapi.Parameter('title_ru', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="Sarlavha (RU)"),
            openapi.Parameter('short_description_uz', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="Qisqa tavsif (UZ)"),
            openapi.Parameter('short_description_ru', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="Qisqa tavsif (RU)"),
            openapi.Parameter('content_uz', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="To'liq matn (UZ)"),
            openapi.Parameter('content_ru', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="To'liq matn (RU)"),
            openapi.Parameter('image', openapi.IN_FORM, type=openapi.TYPE_FILE, required=False, description="Asosiy rasm"),
            openapi.Parameter('status', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, enum=['draft', 'published', 'archived']),
            openapi.Parameter('is_featured', openapi.IN_FORM, type=openapi.TYPE_BOOLEAN, required=False),
            openapi.Parameter('published_at', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="Nashr sanasi (ISO 8601)"),
        ],
        consumes=['multipart/form-data'],
        responses={200: NewsSerializer, 400: openapi.Response(description="Validatsiya xatosi")},
        tags=['Content - News'],
    )
    def patch(self, request, *args, **kwargs):
        obj = self.get_object()
        serializer = NewsWriteSerializer(obj, data=request.data, partial=True, context={'request': request})
        serializer.is_valid(raise_exception=True)
        obj = serializer.save()
        return Response(NewsSerializer(obj, context={'request': request}).data)

    @swagger_auto_schema(
        operation_summary="Yangilikni o'chirish",
        responses={200: openapi.Response(description="Muvaffaqiyatli o'chirildi")},
        tags=['Content - News'],
    )
    def delete(self, request, *args, **kwargs):
        obj = self.get_object()
        data = {
            'id': obj.id,
            'slug': obj.slug,
            'title': obj.title_uz or obj.title_ru or '',
            'detail': "Yangilik muvaffaqiyatli o'chirildi.",
        }
        obj.delete()
        return Response(data, status=status.HTTP_200_OK)


# ─────────────────────────────────────────────────────────────────────────────
# Announcement
# ─────────────────────────────────────────────────────────────────────────────

class AnnouncementListCreateAPIView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticatedOrReadOnly]
    pagination_class = ContentPagination
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'is_important']
    search_fields = [
        'title_uz', 'title_ru',
        'short_description_uz', 'short_description_ru',
    ]
    ordering_fields = ['created_at', 'published_at', 'expires_at', 'views_count']
    ordering = ['-published_at', '-created_at']

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Announcement.objects.none()
        qs = Announcement.objects.select_related('created_by').all()
        if self.request.query_params.get('active_only', '').lower() == 'true':
            qs = qs.filter(
                Q(expires_at__isnull=True) | Q(expires_at__gt=timezone.now())
            )
        return qs

    def get_serializer_class(self):
        if getattr(self, 'swagger_fake_view', False):
            return AnnouncementSerializer
        return AnnouncementWriteSerializer if self.request.method == 'POST' else AnnouncementSerializer

    @swagger_auto_schema(
        operation_summary="E'lonlar ro'yxati",
        operation_description=(
            "Barcha e'lonlar. Filterlar:\n"
            "- `?status=draft|published|archived`\n"
            "- `?is_important=true|false`\n"
            "- `?active_only=true` — muddati o'tmagan e'lonlar\n"
            "- `?search=...` — sarlavha/tavsif bo'yicha qidirish\n"
            "- `?lang=uz|ru` — faqat o'sha tildagi tarjima"
        ),
        manual_parameters=[LANG_PARAM, ACTIVE_ONLY_PARAM],
        responses={200: AnnouncementSerializer(many=True)},
        tags=['Content - Announcements'],
    )
    def get(self, request, *args, **kwargs):
        lang = request.query_params.get('lang')
        qs = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(qs)
        if page is not None:
            data = AnnouncementSerializer(page, many=True, context={'request': request}).data
            return self.get_paginated_response(apply_lang_filter(list(data), lang))
        data = AnnouncementSerializer(qs, many=True, context={'request': request}).data
        return Response(apply_lang_filter(list(data), lang))

    @swagger_auto_schema(
        operation_summary="Yangi e'lon yaratish",
        operation_description=(
            "Autentifikatsiya talab qilinadi. **`multipart/form-data`** orqali yuboriladi.\n\n"
            "Kamida bitta tilda `title_*` to'ldirilishi shart."
        ),
        manual_parameters=[
            openapi.Parameter('title_uz', openapi.IN_FORM, type=openapi.TYPE_STRING, required=True, description="Sarlavha (UZ)"),
            openapi.Parameter('title_ru', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="Sarlavha (RU)"),
            openapi.Parameter('short_description_uz', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="Qisqa tavsif (UZ)"),
            openapi.Parameter('short_description_ru', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="Qisqa tavsif (RU)"),
            openapi.Parameter('content_uz', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="To'liq matn (UZ)"),
            openapi.Parameter('content_ru', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="To'liq matn (RU)"),
            openapi.Parameter('image', openapi.IN_FORM, type=openapi.TYPE_FILE, required=False, description="Asosiy rasm"),
            openapi.Parameter('status', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, enum=['draft','published','archived'], default='draft'),
            openapi.Parameter('is_important', openapi.IN_FORM, type=openapi.TYPE_BOOLEAN, required=False, default=False),
            openapi.Parameter('expires_at', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="Muddati tugash sanasi (ISO 8601)"),
            openapi.Parameter('published_at', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="Nashr sanasi (ISO 8601)"),
        ],
        consumes=['multipart/form-data'],
        responses={
            201: AnnouncementSerializer,
            400: openapi.Response(description="Validatsiya xatosi"),
            401: openapi.Response(description="Autentifikatsiya talab qilinadi"),
        },
        tags=['Content - Announcements'],
    )
    def post(self, request, *args, **kwargs):
        serializer = AnnouncementWriteSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        ann = serializer.save()
        return Response(
            AnnouncementSerializer(ann, context={'request': request}).data,
            status=status.HTTP_201_CREATED,
        )


class AnnouncementDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticatedOrReadOnly]
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    lookup_field = 'slug'

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Announcement.objects.none()
        return Announcement.objects.select_related('created_by').all()

    def get_serializer_class(self):
        if getattr(self, 'swagger_fake_view', False):
            return AnnouncementSerializer
        if self.request.method in ('PUT', 'PATCH'):
            return AnnouncementWriteSerializer
        return AnnouncementSerializer

    @swagger_auto_schema(
        operation_summary="E'lon detali",
        operation_description="Bitta e'lon. Ko'rishlar soni avtomatik oshadi. ?lang= bilan til filtri.",
        manual_parameters=[LANG_PARAM],
        responses={200: AnnouncementSerializer, 404: openapi.Response(description="Topilmadi")},
        tags=['Content - Announcements'],
    )
    def get(self, request, *args, **kwargs):
        obj = self.get_object()
        Announcement.objects.filter(pk=obj.pk).update(views_count=F('views_count') + 1)
        obj.refresh_from_db()
        lang = request.query_params.get('lang')
        data = AnnouncementSerializer(obj, context={'request': request}).data
        return Response(apply_lang_filter(data, lang))

    @swagger_auto_schema(
        operation_summary="E'lonni to'liq yangilash",
        operation_description="Faqat autentifikatsiyadan o'tgan foydalanuvchi. **`multipart/form-data`** orqali yuboriladi.",
        manual_parameters=[
            openapi.Parameter('title_uz', openapi.IN_FORM, type=openapi.TYPE_STRING, required=True, description="Sarlavha (UZ)"),
            openapi.Parameter('title_ru', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="Sarlavha (RU)"),
            openapi.Parameter('short_description_uz', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="Qisqa tavsif (UZ)"),
            openapi.Parameter('short_description_ru', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="Qisqa tavsif (RU)"),
            openapi.Parameter('content_uz', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="To'liq matn (UZ)"),
            openapi.Parameter('content_ru', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="To'liq matn (RU)"),
            openapi.Parameter('image', openapi.IN_FORM, type=openapi.TYPE_FILE, required=False, description="Asosiy rasm"),
            openapi.Parameter('status', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, enum=['draft','published','archived'], default='draft'),
            openapi.Parameter('is_important', openapi.IN_FORM, type=openapi.TYPE_BOOLEAN, required=False, default=False),
            openapi.Parameter('expires_at', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="Muddati tugash sanasi (ISO 8601)"),
            openapi.Parameter('published_at', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="Nashr sanasi (ISO 8601)"),
        ],
        consumes=['multipart/form-data'],
        responses={200: AnnouncementSerializer, 400: openapi.Response(description="Validatsiya xatosi")},
        tags=['Content - Announcements'],
    )
    def put(self, request, *args, **kwargs):
        obj = self.get_object()
        serializer = AnnouncementWriteSerializer(obj, data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        obj = serializer.save()
        return Response(AnnouncementSerializer(obj, context={'request': request}).data)

    @swagger_auto_schema(
        operation_summary="E'lonni qisman yangilash",
        operation_description="Faqat autentifikatsiyadan o'tgan foydalanuvchi. Faqat o'zgartirilishi kerak bo'lgan maydonlar. **`multipart/form-data`**.",
        manual_parameters=[
            openapi.Parameter('title_uz', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="Sarlavha (UZ)"),
            openapi.Parameter('title_ru', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="Sarlavha (RU)"),
            openapi.Parameter('short_description_uz', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="Qisqa tavsif (UZ)"),
            openapi.Parameter('short_description_ru', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="Qisqa tavsif (RU)"),
            openapi.Parameter('content_uz', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="To'liq matn (UZ)"),
            openapi.Parameter('content_ru', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="To'liq matn (RU)"),
            openapi.Parameter('image', openapi.IN_FORM, type=openapi.TYPE_FILE, required=False, description="Asosiy rasm"),
            openapi.Parameter('status', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, enum=['draft','published','archived']),
            openapi.Parameter('is_important', openapi.IN_FORM, type=openapi.TYPE_BOOLEAN, required=False),
            openapi.Parameter('expires_at', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="Muddati tugash sanasi (ISO 8601)"),
            openapi.Parameter('published_at', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="Nashr sanasi (ISO 8601)"),
        ],
        consumes=['multipart/form-data'],
        responses={200: AnnouncementSerializer, 400: openapi.Response(description="Validatsiya xatosi")},
        tags=['Content - Announcements'],
    )
    def patch(self, request, *args, **kwargs):
        obj = self.get_object()
        serializer = AnnouncementWriteSerializer(obj, data=request.data, partial=True, context={'request': request})
        serializer.is_valid(raise_exception=True)
        obj = serializer.save()
        return Response(AnnouncementSerializer(obj, context={'request': request}).data)

    @swagger_auto_schema(
        operation_summary="E'lonni o'chirish",
        responses={200: openapi.Response(description="Muvaffaqiyatli o'chirildi")},
        tags=['Content - Announcements'],
    )
    def delete(self, request, *args, **kwargs):
        obj = self.get_object()
        data = {
            'id': obj.id,
            'slug': obj.slug,
            'title': obj.title_uz or obj.title_ru or '',
            'detail': "E'lon muvaffaqiyatli o'chirildi.",
        }
        obj.delete()
        return Response(data, status=status.HTTP_200_OK)
