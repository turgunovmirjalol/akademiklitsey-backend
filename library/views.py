from rest_framework import generics, filters, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django_filters.rest_framework import DjangoFilterBackend
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from accounts.permissions import IsAdminOrReadOnly
from .models import LibraryResource, LibraryStats
from .serializers import (
    LibraryResourceSerializer,
    LibraryResourceWriteSerializer,
    LibraryStatsSerializer,
    LibraryStatsWriteSerializer,
    apply_lang_filter,
)

LANGS = ['uz', 'ru']

LANG_PARAM = openapi.Parameter(
    'lang', openapi.IN_QUERY,
    description="Javob tilini filtrlash: uz | ru",
    type=openapi.TYPE_STRING,
    enum=['uz', 'ru'],
    required=False,
)


# ─────────────────────────────────────────────────────────────────────────────
# LibraryStats
# ─────────────────────────────────────────────────────────────────────────────

class LibraryStatsView(APIView):
    """
    Kutubxona statistikasi — singleton.
    GET  — hamma uchun ochiq
    PUT  — faqat admin (qisman yangilash ham qo'llab-quvvatlanadi)
    """
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_permissions(self):
        if self.request.method == 'GET':
            return [AllowAny()]
        return [IsAdminOrReadOnly()]

    @swagger_auto_schema(
        operation_summary="Kutubxona statistikasi",
        operation_description="Kitoblar, elektron resurslar, jurnallar va o'quv qo'llanmalari soni.",
        responses={200: LibraryStatsSerializer},
        tags=['Library - Stats'],
    )
    def get(self, request):
        obj = LibraryStats.get_instance()
        return Response(LibraryStatsSerializer(obj).data)

    @swagger_auto_schema(
        operation_summary="Kutubxona statistikasini yangilash",
        operation_description="Faqat admin. Partial update qo'llab-quvvatlanadi.",
        request_body=LibraryStatsWriteSerializer,
        responses={200: LibraryStatsSerializer},
        tags=['Library - Stats'],
    )
    def put(self, request):
        obj = LibraryStats.get_instance()
        serializer = LibraryStatsWriteSerializer(obj, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        obj = serializer.save()
        return Response(LibraryStatsSerializer(obj).data)


# ─────────────────────────────────────────────────────────────────────────────
# LibraryResource — List & Create
# ─────────────────────────────────────────────────────────────────────────────

class LibraryResourceListView(generics.ListCreateAPIView):
    """
    Kutubxona resurslari ro'yxati va yaratish.
    GET  — hamma uchun ochiq
    POST — faqat admin
    """
    permission_classes = [IsAdminOrReadOnly]
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'file_type', 'is_featured', 'is_active']
    search_fields = ['title_uz', 'title_ru', 'author']
    ordering_fields = ['sort_order', 'created_at', 'download_count']
    ordering = ['sort_order', '-created_at']

    def get_queryset(self):
        return LibraryResource.objects.all()

    def get_serializer_class(self):
        if getattr(self, 'swagger_fake_view', False):
            return LibraryResourceSerializer
        return LibraryResourceWriteSerializer if self.request.method == 'POST' else LibraryResourceSerializer

    @swagger_auto_schema(
        operation_summary="Kutubxona resurslari ro'yxati",
        operation_description=(
            "Barcha resurslar. Filterlar:\n"
            "- `?category=darslik|qollanma|jurnal|amaliy|elektron|boshqa`\n"
            "- `?file_type=pdf|docx|xlsx|pptx|other`\n"
            "- `?is_featured=true|false`\n"
            "- `?is_active=true|false`\n"
            "- `?search=...` — nom yoki muallif bo'yicha\n"
            "- `?lang=uz|ru`"
        ),
        manual_parameters=[LANG_PARAM],
        responses={200: LibraryResourceSerializer(many=True)},
        tags=['Library - Resources'],
    )
    def get(self, request, *args, **kwargs):
        lang = request.query_params.get('lang')
        qs = self.filter_queryset(self.get_queryset())
        data = LibraryResourceSerializer(qs, many=True, context={'request': request}).data
        return Response(apply_lang_filter(data, lang))

    @swagger_auto_schema(
        operation_summary="Yangi resurs yaratish",
        operation_description="Faqat admin. `multipart/form-data` orqali yuboriladi.",
        manual_parameters=[
            openapi.Parameter('title_uz', openapi.IN_FORM, type=openapi.TYPE_STRING, required=True, description="Nomi (UZ)"),
            openapi.Parameter('title_ru', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="Nomi (RU)"),
            openapi.Parameter('description_uz', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="Tavsif (UZ)"),
            openapi.Parameter('description_ru', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="Tavsif (RU)"),
            openapi.Parameter('author', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="Muallif"),
            openapi.Parameter('category', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False,
                              enum=['darslik', 'qollanma', 'jurnal', 'amaliy', 'elektron', 'boshqa'], default='darslik'),
            openapi.Parameter('file_type', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False,
                              enum=['pdf', 'docx', 'xlsx', 'pptx', 'other'], default='pdf'),
            openapi.Parameter('file', openapi.IN_FORM, type=openapi.TYPE_FILE, required=False, description="Resurs fayli"),
            openapi.Parameter('cover_image', openapi.IN_FORM, type=openapi.TYPE_FILE, required=False, description="Muqova rasmi"),
            openapi.Parameter('is_featured', openapi.IN_FORM, type=openapi.TYPE_BOOLEAN, required=False, default=False),
            openapi.Parameter('is_active', openapi.IN_FORM, type=openapi.TYPE_BOOLEAN, required=False, default=True),
            openapi.Parameter('sort_order', openapi.IN_FORM, type=openapi.TYPE_INTEGER, required=False, default=0),
        ],
        consumes=['multipart/form-data'],
        responses={
            201: LibraryResourceSerializer,
            400: openapi.Response(description="Validatsiya xatosi"),
        },
        tags=['Library - Resources'],
    )
    def post(self, request, *args, **kwargs):
        serializer = LibraryResourceWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        obj = serializer.save()
        return Response(
            LibraryResourceSerializer(obj, context={'request': request}).data,
            status=status.HTTP_201_CREATED,
        )


# ─────────────────────────────────────────────────────────────────────────────
# LibraryResource — Detail (retrieve & update only, no delete from API)
# ─────────────────────────────────────────────────────────────────────────────

class LibraryResourceDetailView(generics.RetrieveUpdateAPIView):
    """
    Bitta resurs — ko'rish va tahrirlash.
    GET   — hamma uchun ochiq
    PUT   — faqat admin (to'liq yangilash)
    PATCH — faqat admin (qisman yangilash)
    """
    permission_classes = [IsAdminOrReadOnly]
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    queryset = LibraryResource.objects.all()

    def get_serializer_class(self):
        if getattr(self, 'swagger_fake_view', False):
            return LibraryResourceSerializer
        if self.request.method in ('PUT', 'PATCH'):
            return LibraryResourceWriteSerializer
        return LibraryResourceSerializer

    @swagger_auto_schema(
        operation_summary="Resurs detali",
        manual_parameters=[LANG_PARAM],
        responses={200: LibraryResourceSerializer},
        tags=['Library - Resources'],
    )
    def get(self, request, *args, **kwargs):
        obj = self.get_object()
        lang = request.query_params.get('lang')
        data = LibraryResourceSerializer(obj, context={'request': request}).data
        return Response(apply_lang_filter(data, lang))

    @swagger_auto_schema(
        operation_summary="Resursni to'liq yangilash",
        operation_description="Faqat admin. `multipart/form-data`.",
        manual_parameters=[
            openapi.Parameter('title_uz', openapi.IN_FORM, type=openapi.TYPE_STRING, required=True, description="Nomi (UZ)"),
            openapi.Parameter('title_ru', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="Nomi (RU)"),
            openapi.Parameter('description_uz', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="Tavsif (UZ)"),
            openapi.Parameter('description_ru', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="Tavsif (RU)"),
            openapi.Parameter('author', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="Muallif"),
            openapi.Parameter('category', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False,
                              enum=['darslik', 'qollanma', 'jurnal', 'amaliy', 'elektron', 'boshqa']),
            openapi.Parameter('file_type', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False,
                              enum=['pdf', 'docx', 'xlsx', 'pptx', 'other']),
            openapi.Parameter('file', openapi.IN_FORM, type=openapi.TYPE_FILE, required=False, description="Resurs fayli"),
            openapi.Parameter('cover_image', openapi.IN_FORM, type=openapi.TYPE_FILE, required=False, description="Muqova rasmi"),
            openapi.Parameter('is_featured', openapi.IN_FORM, type=openapi.TYPE_BOOLEAN, required=False),
            openapi.Parameter('is_active', openapi.IN_FORM, type=openapi.TYPE_BOOLEAN, required=False),
            openapi.Parameter('sort_order', openapi.IN_FORM, type=openapi.TYPE_INTEGER, required=False),
        ],
        consumes=['multipart/form-data'],
        responses={200: LibraryResourceSerializer},
        tags=['Library - Resources'],
    )
    def put(self, request, *args, **kwargs):
        obj = self.get_object()
        serializer = LibraryResourceWriteSerializer(obj, data=request.data)
        serializer.is_valid(raise_exception=True)
        obj = serializer.save()
        return Response(LibraryResourceSerializer(obj, context={'request': request}).data)

    @swagger_auto_schema(
        operation_summary="Resursni qisman yangilash",
        operation_description="Faqat admin. Faqat o'zgartirilishi kerak bo'lgan maydonlar.",
        manual_parameters=[
            openapi.Parameter('title_uz', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="Nomi (UZ)"),
            openapi.Parameter('title_ru', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="Nomi (RU)"),
            openapi.Parameter('description_uz', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="Tavsif (UZ)"),
            openapi.Parameter('description_ru', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="Tavsif (RU)"),
            openapi.Parameter('author', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="Muallif"),
            openapi.Parameter('category', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False,
                              enum=['darslik', 'qollanma', 'jurnal', 'amaliy', 'elektron', 'boshqa']),
            openapi.Parameter('file_type', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False,
                              enum=['pdf', 'docx', 'xlsx', 'pptx', 'other']),
            openapi.Parameter('file', openapi.IN_FORM, type=openapi.TYPE_FILE, required=False, description="Resurs fayli"),
            openapi.Parameter('cover_image', openapi.IN_FORM, type=openapi.TYPE_FILE, required=False, description="Muqova rasmi"),
            openapi.Parameter('is_featured', openapi.IN_FORM, type=openapi.TYPE_BOOLEAN, required=False),
            openapi.Parameter('is_active', openapi.IN_FORM, type=openapi.TYPE_BOOLEAN, required=False),
            openapi.Parameter('sort_order', openapi.IN_FORM, type=openapi.TYPE_INTEGER, required=False),
        ],
        consumes=['multipart/form-data'],
        responses={200: LibraryResourceSerializer},
        tags=['Library - Resources'],
    )
    def patch(self, request, *args, **kwargs):
        obj = self.get_object()
        serializer = LibraryResourceWriteSerializer(obj, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        obj = serializer.save()
        return Response(LibraryResourceSerializer(obj, context={'request': request}).data)
