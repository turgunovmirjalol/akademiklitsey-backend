from rest_framework import generics, filters, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.pagination import PageNumberPagination
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from accounts.permissions import IsAdminOrReadOnly
from .models import Department, Teacher, Management
from .serializers import (
    DepartmentSerializer, DepartmentDetailSerializer, DepartmentWriteSerializer,
    TeacherSerializer, TeacherWriteSerializer,
    ManagementSerializer, ManagementWriteSerializer,
    apply_lang_filter,
)

# ─── Swagger parametrlar ─────────────────────────────────────────────────────

LANG_PARAM = openapi.Parameter(
    'lang', openapi.IN_QUERY,
    description="Javob tilini filtrlash: uz | uz_cyrl | ru | en",
    type=openapi.TYPE_STRING,
    enum=['uz', 'uz_cyrl', 'ru', 'en'],
    required=False,
)


# ─── Pagination ──────────────────────────────────────────────────────────────

class StructurePagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


# ─────────────────────────────────────────────────────────────────────────────
# Department
# ─────────────────────────────────────────────────────────────────────────────

class DepartmentListView(generics.ListCreateAPIView):
    permission_classes = [IsAdminOrReadOnly]
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_active']
    search_fields = ['name_uz', 'name_ru', 'name_en', 'description_uz']
    ordering_fields = ['sort_order', 'name_uz', 'created_at']
    ordering = ['sort_order', 'name_uz']

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Department.objects.none()
        qs = Department.objects.select_related('head_teacher').all()
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
            return DepartmentSerializer
        return DepartmentWriteSerializer if self.request.method == 'POST' else DepartmentSerializer

    @swagger_auto_schema(
        operation_summary="Kafedralar ro'yxati",
        operation_description=(
            "Barcha kafedralar.\n\n"
            "- `?is_active=true|false` (admin uchun)\n"
            "- `?search=...` — nom bo'yicha qidirish\n"
            "- `?lang=uz|ru|en|uz_cyrl` — faqat o'sha tildagi tarjima"
        ),
        manual_parameters=[LANG_PARAM],
        responses={200: DepartmentSerializer(many=True)},
        tags=["Structure - Departments"],
    )
    def get(self, request, *args, **kwargs):
        lang = request.query_params.get('lang')
        qs = self.filter_queryset(self.get_queryset())
        data = DepartmentSerializer(qs, many=True, context={'request': request}).data
        return Response(apply_lang_filter(list(data), lang))

    @swagger_auto_schema(
        operation_summary="Yangi kafedra yaratish",
        operation_description="Faqat admin. Kamida bitta tilda `name_*` to'ldirilishi shart.",
        request_body=DepartmentWriteSerializer,
        responses={201: DepartmentSerializer, 400: openapi.Response(description="Validatsiya xatosi")},
        tags=["Structure - Departments"],
    )
    def post(self, request, *args, **kwargs):
        serializer = DepartmentWriteSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        dept = serializer.save()
        return Response(
            DepartmentSerializer(dept, context={'request': request}).data,
            status=status.HTTP_201_CREATED,
        )


class DepartmentDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAdminOrReadOnly]
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    lookup_field = 'slug'

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Department.objects.none()
        return Department.objects.select_related('head_teacher').prefetch_related('teachers').all()

    def get_serializer_class(self):
        if getattr(self, 'swagger_fake_view', False):
            return DepartmentDetailSerializer
        if self.request.method in ('PUT', 'PATCH'):
            return DepartmentWriteSerializer
        return DepartmentDetailSerializer

    @swagger_auto_schema(
        operation_summary="Kafedra detali (o'qituvchilar bilan)",
        manual_parameters=[LANG_PARAM],
        responses={200: DepartmentDetailSerializer, 404: openapi.Response(description="Topilmadi")},
        tags=["Structure - Departments"],
    )
    def get(self, request, *args, **kwargs):
        obj = self.get_object()
        lang = request.query_params.get('lang')
        data = DepartmentDetailSerializer(obj, context={'request': request}).data
        return Response(apply_lang_filter(data, lang))

    @swagger_auto_schema(
        operation_summary="Kafedrani to'liq yangilash",
        operation_description="Faqat admin. **`multipart/form-data`** yoki JSON orqali yuboriladi.",
        request_body=DepartmentWriteSerializer,
        responses={200: DepartmentDetailSerializer},
        tags=["Structure - Departments"],
    )
    def put(self, request, *args, **kwargs):
        obj = self.get_object()
        serializer = DepartmentWriteSerializer(obj, data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        obj = serializer.save()
        return Response(DepartmentDetailSerializer(obj, context={'request': request}).data)

    @swagger_auto_schema(
        operation_summary="Kafedrani qisman yangilash",
        operation_description="Faqat admin. Faqat o'zgartiriladigan maydonlarni yuboring.",
        request_body=DepartmentWriteSerializer,
        responses={200: DepartmentDetailSerializer},
        tags=["Structure - Departments"],
    )
    def patch(self, request, *args, **kwargs):
        obj = self.get_object()
        serializer = DepartmentWriteSerializer(obj, data=request.data, partial=True, context={'request': request})
        serializer.is_valid(raise_exception=True)
        obj = serializer.save()
        return Response(DepartmentDetailSerializer(obj, context={'request': request}).data)

    @swagger_auto_schema(
        operation_summary="Kafedrani o'chirish",
        responses={200: openapi.Response(description="O'chirildi")},
        tags=["Structure - Departments"],
    )
    def delete(self, request, *args, **kwargs):
        obj = self.get_object()
        name = obj.name_uz or obj.name_ru or obj.name_en or ''
        obj.delete()
        return Response(
            {'slug': self.kwargs['slug'], 'name': name, 'detail': "Kafedra muvaffaqiyatli o'chirildi."},
            status=status.HTTP_200_OK,
        )


# ─────────────────────────────────────────────────────────────────────────────
# Teacher
# ─────────────────────────────────────────────────────────────────────────────

class TeacherListView(generics.ListCreateAPIView):
    permission_classes = [IsAdminOrReadOnly]
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    pagination_class = StructurePagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['department', 'category', 'is_active']
    search_fields = ['full_name', 'position_uz', 'position_ru', 'subject_uz', 'subject_ru']
    ordering_fields = ['sort_order', 'full_name', 'experience_years', 'created_at']
    ordering = ['sort_order', 'full_name']

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Teacher.objects.none()
        qs = Teacher.objects.select_related('department').all()
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
            return TeacherSerializer
        return TeacherWriteSerializer if self.request.method == 'POST' else TeacherSerializer

    @swagger_auto_schema(
        operation_summary="O'qituvchilar ro'yxati",
        operation_description=(
            "Barcha o'qituvchilar.\n\n"
            "- `?department=<id>` — kafedra bo'yicha filter\n"
            "- `?category=highest|first|second|none`\n"
            "- `?is_active=true|false` (admin uchun)\n"
            "- `?search=...` — ism/lavozim bo'yicha qidirish\n"
            "- `?lang=uz|ru|en|uz_cyrl` — faqat o'sha tildagi tarjima"
        ),
        manual_parameters=[LANG_PARAM],
        responses={200: TeacherSerializer(many=True)},
        tags=["Structure - Teachers"],
    )
    def get(self, request, *args, **kwargs):
        lang = request.query_params.get('lang')
        qs = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(qs)
        if page is not None:
            data = TeacherSerializer(page, many=True, context={'request': request}).data
            return self.get_paginated_response(apply_lang_filter(list(data), lang))
        data = TeacherSerializer(qs, many=True, context={'request': request}).data
        return Response(apply_lang_filter(list(data), lang))

    @swagger_auto_schema(
        operation_summary="Yangi o'qituvchi qo'shish",
        operation_description=(
            "Faqat admin. **`multipart/form-data`** orqali yuboriladi.\n\n"
            "Kamida bitta tilda `position_*` to'ldirilishi shart."
        ),
        manual_parameters=[
            openapi.Parameter('full_name', openapi.IN_FORM, type=openapi.TYPE_STRING, required=True, description="To'liq ismi"),
            openapi.Parameter('position_uz', openapi.IN_FORM, type=openapi.TYPE_STRING, required=True, description="Lavozimi (UZ)"),
            openapi.Parameter('position_uz_cyrl', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="Lavozimi (UZ Kirill)"),
            openapi.Parameter('position_ru', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="Lavozimi (RU)"),
            openapi.Parameter('position_en', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="Lavozimi (EN)"),
            openapi.Parameter('subject_uz', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="Fan (UZ)"),
            openapi.Parameter('subject_uz_cyrl', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="Fan (UZ Kirill)"),
            openapi.Parameter('subject_ru', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="Fan (RU)"),
            openapi.Parameter('subject_en', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="Fan (EN)"),
            openapi.Parameter('bio_uz', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="Tarjimai hol (UZ)"),
            openapi.Parameter('bio_uz_cyrl', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="Tarjimai hol (UZ Kirill)"),
            openapi.Parameter('bio_ru', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="Tarjimai hol (RU)"),
            openapi.Parameter('bio_en', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="Tarjimai hol (EN)"),
            openapi.Parameter('achievements_uz', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="Yutuqlar (UZ)"),
            openapi.Parameter('achievements_uz_cyrl', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="Yutuqlar (UZ Kirill)"),
            openapi.Parameter('achievements_ru', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="Yutuqlar (RU)"),
            openapi.Parameter('achievements_en', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="Yutuqlar (EN)"),
            openapi.Parameter('academic_degree', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False),
            openapi.Parameter('academic_rank', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="Akademik unvon (ixtiyoriy)"),
            openapi.Parameter('category', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, enum=['highest','first','second','none'], default='none'),
            openapi.Parameter('experience_years', openapi.IN_FORM, type=openapi.TYPE_INTEGER, required=False),
            openapi.Parameter('department', openapi.IN_FORM, type=openapi.TYPE_INTEGER, required=False, description="Kafedra ID"),
            openapi.Parameter('photo', openapi.IN_FORM, type=openapi.TYPE_FILE, required=False, description="Rasm"),
            openapi.Parameter('email', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False),
            openapi.Parameter('is_active', openapi.IN_FORM, type=openapi.TYPE_BOOLEAN, required=False, default=True),
            openapi.Parameter('sort_order', openapi.IN_FORM, type=openapi.TYPE_INTEGER, required=False, default=0),
        ],
        consumes=['multipart/form-data'],
        responses={201: TeacherSerializer, 400: openapi.Response(description="Validatsiya xatosi")},
        tags=["Structure - Teachers"],
    )
    def post(self, request, *args, **kwargs):
        serializer = TeacherWriteSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        teacher = serializer.save()
        return Response(
            TeacherSerializer(teacher, context={'request': request}).data,
            status=status.HTTP_201_CREATED,
        )


class TeacherDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAdminOrReadOnly]
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    lookup_field = 'slug'

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Teacher.objects.none()
        return Teacher.objects.select_related('department').all()

    def get_serializer_class(self):
        if getattr(self, 'swagger_fake_view', False):
            return TeacherSerializer
        if self.request.method in ('PUT', 'PATCH'):
            return TeacherWriteSerializer
        return TeacherSerializer

    @swagger_auto_schema(
        operation_summary="O'qituvchi detali",
        manual_parameters=[LANG_PARAM],
        responses={200: TeacherSerializer, 404: openapi.Response(description="Topilmadi")},
        tags=["Structure - Teachers"],
    )
    def get(self, request, *args, **kwargs):
        obj = self.get_object()
        lang = request.query_params.get('lang')
        data = TeacherSerializer(obj, context={'request': request}).data
        return Response(apply_lang_filter(data, lang))

    @swagger_auto_schema(
        operation_summary="O'qituvchini to'liq yangilash",
        operation_description="Faqat admin. **`multipart/form-data`** orqali yuboriladi.",
        manual_parameters=[
            openapi.Parameter('full_name', openapi.IN_FORM, type=openapi.TYPE_STRING, required=True),
            openapi.Parameter('position_uz', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False),
            openapi.Parameter('position_uz_cyrl', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False),
            openapi.Parameter('position_ru', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False),
            openapi.Parameter('position_en', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False),
            openapi.Parameter('subject_uz', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False),
            openapi.Parameter('subject_uz_cyrl', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False),
            openapi.Parameter('subject_ru', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False),
            openapi.Parameter('subject_en', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False),
            openapi.Parameter('bio_uz', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False),
            openapi.Parameter('bio_uz_cyrl', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False),
            openapi.Parameter('bio_ru', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False),
            openapi.Parameter('bio_en', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False),
            openapi.Parameter('achievements_uz', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False),
            openapi.Parameter('achievements_uz_cyrl', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False),
            openapi.Parameter('achievements_ru', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False),
            openapi.Parameter('achievements_en', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False),
            openapi.Parameter('academic_degree', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False),
            openapi.Parameter('academic_rank', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False),
            openapi.Parameter('category', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, enum=['highest','first','second','none']),
            openapi.Parameter('experience_years', openapi.IN_FORM, type=openapi.TYPE_INTEGER, required=False),
            openapi.Parameter('department', openapi.IN_FORM, type=openapi.TYPE_INTEGER, required=False),
            openapi.Parameter('photo', openapi.IN_FORM, type=openapi.TYPE_FILE, required=False),
            openapi.Parameter('email', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False),
            openapi.Parameter('is_active', openapi.IN_FORM, type=openapi.TYPE_BOOLEAN, required=False),
            openapi.Parameter('sort_order', openapi.IN_FORM, type=openapi.TYPE_INTEGER, required=False),
        ],
        consumes=['multipart/form-data'],
        responses={200: TeacherSerializer},
        tags=["Structure - Teachers"],
    )
    def put(self, request, *args, **kwargs):
        obj = self.get_object()
        serializer = TeacherWriteSerializer(obj, data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        obj = serializer.save()
        return Response(TeacherSerializer(obj, context={'request': request}).data)

    @swagger_auto_schema(
        operation_summary="O'qituvchini qisman yangilash",
        operation_description="Faqat admin. **`multipart/form-data`** orqali yuboriladi. Faqat o'zgartiriladigan maydonlarni yuboring.",
        manual_parameters=[
            openapi.Parameter('full_name', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False),
            openapi.Parameter('position_uz', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False),
            openapi.Parameter('position_uz_cyrl', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False),
            openapi.Parameter('position_ru', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False),
            openapi.Parameter('position_en', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False),
            openapi.Parameter('subject_uz', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False),
            openapi.Parameter('subject_uz_cyrl', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False),
            openapi.Parameter('subject_ru', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False),
            openapi.Parameter('subject_en', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False),
            openapi.Parameter('bio_uz', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False),
            openapi.Parameter('bio_uz_cyrl', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False),
            openapi.Parameter('bio_ru', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False),
            openapi.Parameter('bio_en', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False),
            openapi.Parameter('achievements_uz', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False),
            openapi.Parameter('achievements_uz_cyrl', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False),
            openapi.Parameter('achievements_ru', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False),
            openapi.Parameter('achievements_en', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False),
            openapi.Parameter('academic_degree', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False),
            openapi.Parameter('academic_rank', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False),
            openapi.Parameter('category', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, enum=['highest','first','second','none']),
            openapi.Parameter('experience_years', openapi.IN_FORM, type=openapi.TYPE_INTEGER, required=False),
            openapi.Parameter('department', openapi.IN_FORM, type=openapi.TYPE_INTEGER, required=False),
            openapi.Parameter('photo', openapi.IN_FORM, type=openapi.TYPE_FILE, required=False),
            openapi.Parameter('email', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False),
            openapi.Parameter('is_active', openapi.IN_FORM, type=openapi.TYPE_BOOLEAN, required=False),
            openapi.Parameter('sort_order', openapi.IN_FORM, type=openapi.TYPE_INTEGER, required=False),
        ],
        consumes=['multipart/form-data'],
        responses={200: TeacherSerializer},
        tags=["Structure - Teachers"],
    )
    def patch(self, request, *args, **kwargs):
        obj = self.get_object()
        serializer = TeacherWriteSerializer(obj, data=request.data, partial=True, context={'request': request})
        serializer.is_valid(raise_exception=True)
        obj = serializer.save()
        return Response(TeacherSerializer(obj, context={'request': request}).data)

    @swagger_auto_schema(
        operation_summary="O'qituvchini o'chirish",
        responses={200: openapi.Response(description="O'chirildi")},
        tags=["Structure - Teachers"],
    )
    def delete(self, request, *args, **kwargs):
        obj = self.get_object()
        data = {'id': obj.pk, 'full_name': obj.full_name, 'detail': "O'qituvchi muvaffaqiyatli o'chirildi."}
        obj.delete()
        return Response(data, status=status.HTTP_200_OK)


class TeacherByDepartmentView(generics.ListAPIView):
    """Kafedra bo'yicha o'qituvchilar."""
    permission_classes = [IsAdminOrReadOnly]
    serializer_class = TeacherSerializer

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Teacher.objects.none()
        return Teacher.objects.filter(
            department_id=self.kwargs['department_id'],
            is_active=True,
        ).select_related('department').order_by('sort_order', 'full_name')

    @swagger_auto_schema(
        operation_summary="Kafedra bo'yicha o'qituvchilar",
        manual_parameters=[LANG_PARAM],
        responses={200: TeacherSerializer(many=True)},
        tags=["Structure - Teachers"],
    )
    def get(self, request, *args, **kwargs):
        lang = request.query_params.get('lang')
        qs = self.get_queryset()
        data = TeacherSerializer(qs, many=True, context={'request': request}).data
        return Response(apply_lang_filter(list(data), lang))


# ─────────────────────────────────────────────────────────────────────────────
# Management
# ─────────────────────────────────────────────────────────────────────────────

class ManagementListView(generics.ListCreateAPIView):
    permission_classes = [IsAdminOrReadOnly]
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['full_name', 'position_uz', 'position_ru']
    ordering_fields = ['sort_order']
    ordering = ['sort_order']

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Management.objects.none()
        qs = Management.objects.all()
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
            return ManagementSerializer
        return ManagementWriteSerializer if self.request.method == 'POST' else ManagementSerializer

    @swagger_auto_schema(
        operation_summary="Rahbariyat ro'yxati",
        operation_description="Barcha rahbarlar. ?lang= bilan til filtri.",
        manual_parameters=[LANG_PARAM],
        responses={200: ManagementSerializer(many=True)},
        tags=["Structure - Management"],
    )
    def get(self, request, *args, **kwargs):
        lang = request.query_params.get('lang')
        qs = self.filter_queryset(self.get_queryset())
        data = ManagementSerializer(qs, many=True, context={'request': request}).data
        return Response(apply_lang_filter(list(data), lang))

    @swagger_auto_schema(
        operation_summary="Yangi rahbar qo'shish",
        operation_description=(
            "Faqat admin. **`multipart/form-data`** orqali yuboriladi.\n\n"
            "Kamida bitta tilda `position_*` to'ldirilishi shart."
        ),
        manual_parameters=[
            openapi.Parameter('full_name', openapi.IN_FORM, type=openapi.TYPE_STRING, required=True, description="To'liq ismi"),
            openapi.Parameter('position_uz', openapi.IN_FORM, type=openapi.TYPE_STRING, required=True, description="Lavozimi (UZ)"),
            openapi.Parameter('position_uz_cyrl', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="Lavozimi (UZ Kirill)"),
            openapi.Parameter('position_ru', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="Lavozimi (RU)"),
            openapi.Parameter('position_en', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="Lavozimi (EN)"),
            openapi.Parameter('bio_uz', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="Tarjimai hol (UZ)"),
            openapi.Parameter('bio_uz_cyrl', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="Tarjimai hol (UZ Kirill)"),
            openapi.Parameter('bio_ru', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="Tarjimai hol (RU)"),
            openapi.Parameter('bio_en', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="Tarjimai hol (EN)"),
            openapi.Parameter('reception_hours_uz', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="Qabul vaqti (UZ)"),
            openapi.Parameter('reception_hours_uz_cyrl', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="Qabul vaqti (UZ Kirill)"),
            openapi.Parameter('reception_hours_ru', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="Qabul vaqti (RU)"),
            openapi.Parameter('reception_hours_en', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="Qabul vaqti (EN)"),
            openapi.Parameter('academic_degree', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False),
            openapi.Parameter('phone', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False),
            openapi.Parameter('email', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False),
            openapi.Parameter('photo', openapi.IN_FORM, type=openapi.TYPE_FILE, required=False, description="Rasm"),
            openapi.Parameter('is_active', openapi.IN_FORM, type=openapi.TYPE_BOOLEAN, required=False, default=True),
            openapi.Parameter('sort_order', openapi.IN_FORM, type=openapi.TYPE_INTEGER, required=False, default=0),
        ],
        consumes=['multipart/form-data'],
        responses={201: ManagementSerializer, 400: openapi.Response(description="Validatsiya xatosi")},
        tags=["Structure - Management"],
    )
    def post(self, request, *args, **kwargs):
        serializer = ManagementWriteSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        manager = serializer.save()
        return Response(
            ManagementSerializer(manager, context={'request': request}).data,
            status=status.HTTP_201_CREATED,
        )


class ManagementDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAdminOrReadOnly]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Management.objects.none()
        return Management.objects.all()

    def get_serializer_class(self):
        if getattr(self, 'swagger_fake_view', False):
            return ManagementSerializer
        if self.request.method in ('PUT', 'PATCH'):
            return ManagementWriteSerializer
        return ManagementSerializer

    @swagger_auto_schema(
        operation_summary="Rahbar detali",
        manual_parameters=[LANG_PARAM],
        responses={200: ManagementSerializer, 404: openapi.Response(description="Topilmadi")},
        tags=["Structure - Management"],
    )
    def get(self, request, *args, **kwargs):
        obj = self.get_object()
        lang = request.query_params.get('lang')
        data = ManagementSerializer(obj, context={'request': request}).data
        return Response(apply_lang_filter(data, lang))

    @swagger_auto_schema(
        operation_summary="Rahbarni to'liq yangilash",
        operation_description="Faqat admin. **`multipart/form-data`** orqali yuboriladi.",
        manual_parameters=[
            openapi.Parameter('full_name', openapi.IN_FORM, type=openapi.TYPE_STRING, required=True),
            openapi.Parameter('position_uz', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False),
            openapi.Parameter('position_uz_cyrl', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False),
            openapi.Parameter('position_ru', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False),
            openapi.Parameter('position_en', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False),
            openapi.Parameter('bio_uz', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False),
            openapi.Parameter('bio_uz_cyrl', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False),
            openapi.Parameter('bio_ru', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False),
            openapi.Parameter('bio_en', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False),
            openapi.Parameter('reception_hours_uz', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False),
            openapi.Parameter('reception_hours_uz_cyrl', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False),
            openapi.Parameter('reception_hours_ru', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False),
            openapi.Parameter('reception_hours_en', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False),
            openapi.Parameter('academic_degree', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False),
            openapi.Parameter('phone', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False),
            openapi.Parameter('email', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False),
            openapi.Parameter('photo', openapi.IN_FORM, type=openapi.TYPE_FILE, required=False),
            openapi.Parameter('is_active', openapi.IN_FORM, type=openapi.TYPE_BOOLEAN, required=False),
            openapi.Parameter('sort_order', openapi.IN_FORM, type=openapi.TYPE_INTEGER, required=False),
        ],
        consumes=['multipart/form-data'],
        responses={200: ManagementSerializer},
        tags=["Structure - Management"],
    )
    def put(self, request, *args, **kwargs):
        obj = self.get_object()
        serializer = ManagementWriteSerializer(obj, data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        obj = serializer.save()
        return Response(ManagementSerializer(obj, context={'request': request}).data)

    @swagger_auto_schema(
        operation_summary="Rahbarni qisman yangilash",
        operation_description="Faqat admin. **`multipart/form-data`** orqali yuboriladi. Faqat o'zgartiriladigan maydonlarni yuboring.",
        manual_parameters=[
            openapi.Parameter('full_name', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False),
            openapi.Parameter('position_uz', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False),
            openapi.Parameter('position_uz_cyrl', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False),
            openapi.Parameter('position_ru', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False),
            openapi.Parameter('position_en', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False),
            openapi.Parameter('bio_uz', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False),
            openapi.Parameter('bio_uz_cyrl', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False),
            openapi.Parameter('bio_ru', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False),
            openapi.Parameter('bio_en', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False),
            openapi.Parameter('reception_hours_uz', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False),
            openapi.Parameter('reception_hours_uz_cyrl', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False),
            openapi.Parameter('reception_hours_ru', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False),
            openapi.Parameter('reception_hours_en', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False),
            openapi.Parameter('academic_degree', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False),
            openapi.Parameter('phone', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False),
            openapi.Parameter('email', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False),
            openapi.Parameter('photo', openapi.IN_FORM, type=openapi.TYPE_FILE, required=False),
            openapi.Parameter('is_active', openapi.IN_FORM, type=openapi.TYPE_BOOLEAN, required=False),
            openapi.Parameter('sort_order', openapi.IN_FORM, type=openapi.TYPE_INTEGER, required=False),
        ],
        consumes=['multipart/form-data'],
        responses={200: ManagementSerializer},
        tags=["Structure - Management"],
    )
    def patch(self, request, *args, **kwargs):
        obj = self.get_object()
        serializer = ManagementWriteSerializer(obj, data=request.data, partial=True, context={'request': request})
        serializer.is_valid(raise_exception=True)
        obj = serializer.save()
        return Response(ManagementSerializer(obj, context={'request': request}).data)

    @swagger_auto_schema(
        operation_summary="Rahbarni o'chirish",
        responses={200: openapi.Response(description="O'chirildi")},
        tags=["Structure - Management"],
    )
    def delete(self, request, *args, **kwargs):
        obj = self.get_object()
        data = {'id': obj.pk, 'full_name': obj.full_name, 'detail': "Rahbar muvaffaqiyatli o'chirildi."}
        obj.delete()
        return Response(data, status=status.HTTP_200_OK)
