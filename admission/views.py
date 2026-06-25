"""
Admission app views.

All write endpoints accept multipart/form-data.
Each language field is sent as a separate flat field.
"""
from rest_framework import generics, filters, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from accounts.permissions import IsAdminOrReadOnly
from .models import AdmissionInfo, AdmissionSubject, AdmissionDocument, FAQ, DarsJadvali
from .serializers import (
    AdmissionInfoSerializer,
    AdmissionInfoWriteSerializer,
    AdmissionSubjectSerializer,
    AdmissionSubjectWriteSerializer,
    AdmissionDocumentSerializer,
    AdmissionDocumentWriteSerializer,
    FAQSerializer,
    FAQWriteSerializer,
    DarsJadvaliSerializer,
    DarsJadvaliWriteSerializer,
)

LANGS = ['uz', 'ru']


def apply_lang_filter(serializer_data, lang):
    """When ?lang= is given, show only that language, fallback to uz."""
    if not lang or lang not in LANGS:
        return serializer_data

    def _filter(item):
        if not isinstance(item, dict) or 'translations' not in item:
            return item
        t = item.get('translations') or {}
        chosen = t.get(lang, {})
        if not any(chosen.values()):
            chosen = t.get('uz', {})
        item = dict(item)
        item['translations'] = {lang: chosen}
        return item

    if isinstance(serializer_data, list):
        return [_filter(i) for i in serializer_data]
    return _filter(serializer_data)

# ─── Swagger common parameters ──────────────────────────────────────────────

LANG_PARAM = openapi.Parameter(
    'lang', openapi.IN_QUERY,
    description="Filter response language: uz | ru (optional, if omitted all languages are shown)",
    type=openapi.TYPE_STRING,
    enum=['uz', 'ru'],
    required=False,
)


# ─────────────────────────────────────────────────────────────────────────────
# AdmissionInfo
# ─────────────────────────────────────────────────────────────────────────────

class AdmissionCurrentView(APIView):
    """
    Current active admission info + subjects + documents.
    GET  — open to everyone
    POST — admin only (create new admission)
    PUT  — admin only (update current admission)
    """
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_permissions(self):
        if self.request.method == 'GET':
            return [AllowAny()]
        return [IsAdminOrReadOnly()]

    def _get_active(self):
        return AdmissionInfo.objects.filter(is_active=True).first()

    @swagger_auto_schema(
        operation_summary="Current admission info",
        operation_description=(
            "Returns active admission info, exam subjects and required documents.\n\n"
            "?lang=uz — only in Uzbek\n"
            "?lang=ru — only in Russian"
        ),
        manual_parameters=[LANG_PARAM],
        responses={
            200: openapi.Response(
                description="Success",
                examples={
                    "application/json": {
                        "admission_info": {"id": 1, "academic_year": "2026-2027"},
                        "subjects": [],
                        "documents": [],
                    }
                }
            ),
            404: openapi.Response(description="Active admission not found"),
        },
        tags=['Admission'],
    )
    def get(self, request):
        obj = self._get_active()
        if not obj:
            return Response(
                {"detail": "Current admission info not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        lang = request.query_params.get('lang')
        ctx = {'request': request}
        subjects = AdmissionSubject.objects.order_by('sort_order')
        documents = AdmissionDocument.objects.order_by('sort_order')
        data = {
            'admission_info': AdmissionInfoSerializer(obj, context=ctx).data,
            'subjects': apply_lang_filter(
                AdmissionSubjectSerializer(subjects, many=True, context=ctx).data, lang
            ),
            'documents': apply_lang_filter(
                AdmissionDocumentSerializer(documents, many=True, context=ctx).data, lang
            ),
        }
        return Response(data)

    @swagger_auto_schema(
        operation_summary="Create new admission info",
        operation_description="Admin only. Returns error if active admission already exists.",
        request_body=AdmissionInfoWriteSerializer,
        responses={
            201: AdmissionInfoSerializer,
            400: openapi.Response(description="Validation error or active admission already exists"),
        },
        tags=['Admission'],
    )
    def post(self, request):
        if self._get_active():
            return Response(
                {"detail": "An active admission already exists. Use PUT to update."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer = AdmissionInfoWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        obj = serializer.save()
        return Response(
            AdmissionInfoSerializer(obj, context={'request': request}).data,
            status=status.HTTP_201_CREATED,
        )

    @swagger_auto_schema(
        operation_summary="Update current admission info",
        operation_description="Admin only. Supports partial update.",
        request_body=AdmissionInfoWriteSerializer,
        responses={
            200: AdmissionInfoSerializer,
            404: openapi.Response(description="Active admission not found"),
        },
        tags=['Admission'],
    )
    def put(self, request):
        obj = self._get_active()
        if not obj:
            return Response(
                {"detail": "Current admission info not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = AdmissionInfoWriteSerializer(obj, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        obj = serializer.save()
        return Response(AdmissionInfoSerializer(obj, context={'request': request}).data)


class AdmissionHistoryView(generics.ListAPIView):
    """Past years admission history (inactive records)."""
    permission_classes = [AllowAny]
    serializer_class = AdmissionInfoSerializer
    filter_backends = [filters.OrderingFilter]
    ordering = ['-academic_year']

    def get_queryset(self):
        return AdmissionInfo.objects.filter(is_active=False)

    @swagger_auto_schema(
        operation_summary="Admission history",
        operation_description="Past years admission info (inactive records).",
        tags=['Admission'],
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


# ─────────────────────────────────────────────────────────────────────────────
# AdmissionSubject
# ─────────────────────────────────────────────────────────────────────────────

SUBJECT_WRITE_PARAMS = [
    openapi.Parameter('subject_name_uz', openapi.IN_FORM, type=openapi.TYPE_STRING, required=True, description="Subject name (UZ)"),
    openapi.Parameter('subject_name_ru', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="Subject name (RU)"),
    openapi.Parameter('description_uz', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="Description (UZ)"),
    openapi.Parameter('description_ru', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="Description (RU)"),
    openapi.Parameter('subject_type', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="Subject type"),
    openapi.Parameter('max_score', openapi.IN_FORM, type=openapi.TYPE_INTEGER, required=False, description="Maximum score"),
    openapi.Parameter('sort_order', openapi.IN_FORM, type=openapi.TYPE_INTEGER, required=False, default=0),
]


class AdmissionSubjectListCreateView(generics.ListCreateAPIView):
    """Subjects list and create."""
    permission_classes = [IsAdminOrReadOnly]
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['subject_type']
    search_fields = ['subject_name_uz', 'subject_name_ru', 'description_uz', 'description_ru']
    ordering_fields = ['sort_order', 'subject_name_uz', 'max_score']
    ordering = ['sort_order']

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return AdmissionSubject.objects.none()
        return AdmissionSubject.objects.all()

    def get_serializer_class(self):
        if getattr(self, 'swagger_fake_view', False):
            return AdmissionSubjectSerializer
        return AdmissionSubjectWriteSerializer if self.request.method == 'POST' else AdmissionSubjectSerializer

    @swagger_auto_schema(
        operation_summary="Exam subjects list",
        operation_description=(
            "Exam subjects for current admission.\n\n"
            "- `?is_active=true|false` (for admin)\n"
            "- `?search=...` — search by name/description\n"
            "- `?lang=uz|ru` — show only that language"
        ),
        manual_parameters=[LANG_PARAM],
        responses={200: AdmissionSubjectSerializer(many=True)},
        tags=['Admission - Subjects'],
    )
    def get(self, request, *args, **kwargs):
        lang = request.query_params.get('lang')
        qs = self.filter_queryset(self.get_queryset())
        data = AdmissionSubjectSerializer(qs, many=True, context={'request': request}).data
        return Response(apply_lang_filter(list(data), lang))

    @swagger_auto_schema(
        operation_summary="Create new exam subject",
        operation_description="Admin only. Sent via **`multipart/form-data`**.",
        manual_parameters=SUBJECT_WRITE_PARAMS,
        consumes=['multipart/form-data'],
        responses={
            201: AdmissionSubjectSerializer,
            400: openapi.Response(description="Validation error"),
        },
        tags=['Admission - Subjects'],
    )
    def post(self, request, *args, **kwargs):
        serializer = AdmissionSubjectWriteSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        obj = serializer.save()
        return Response(
            AdmissionSubjectSerializer(obj, context={'request': request}).data,
            status=status.HTTP_201_CREATED,
        )


class AdmissionSubjectDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Single subject — view, edit, delete."""
    permission_classes = [IsAdminOrReadOnly]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return AdmissionSubject.objects.none()
        return AdmissionSubject.objects.all()

    def get_serializer_class(self):
        if getattr(self, 'swagger_fake_view', False):
            return AdmissionSubjectSerializer
        if self.request.method in ('PUT', 'PATCH'):
            return AdmissionSubjectWriteSerializer
        return AdmissionSubjectSerializer

    @swagger_auto_schema(
        operation_summary="Subject detail",
        manual_parameters=[LANG_PARAM],
        responses={200: AdmissionSubjectSerializer, 404: openapi.Response(description="Not found")},
        tags=['Admission - Subjects'],
    )
    def get(self, request, *args, **kwargs):
        obj = self.get_object()
        lang = request.query_params.get('lang')
        data = AdmissionSubjectSerializer(obj, context={'request': request}).data
        return Response(apply_lang_filter(data, lang))

    @swagger_auto_schema(
        operation_summary="Update subject completely",
        operation_description="Admin only. Sent via **`multipart/form-data`**.",
        manual_parameters=SUBJECT_WRITE_PARAMS,
        consumes=['multipart/form-data'],
        responses={200: AdmissionSubjectSerializer, 400: openapi.Response(description="Validation error")},
        tags=['Admission - Subjects'],
    )
    def put(self, request, *args, **kwargs):
        obj = self.get_object()
        serializer = AdmissionSubjectWriteSerializer(obj, data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        obj = serializer.save()
        return Response(AdmissionSubjectSerializer(obj, context={'request': request}).data)

    @swagger_auto_schema(
        operation_summary="Update subject partially",
        operation_description="Admin only. Only modified fields. **`multipart/form-data`**.",
        manual_parameters=SUBJECT_WRITE_PARAMS,
        consumes=['multipart/form-data'],
        responses={200: AdmissionSubjectSerializer, 400: openapi.Response(description="Validation error")},
        tags=['Admission - Subjects'],
    )
    def patch(self, request, *args, **kwargs):
        obj = self.get_object()
        serializer = AdmissionSubjectWriteSerializer(obj, data=request.data, partial=True, context={'request': request})
        serializer.is_valid(raise_exception=True)
        obj = serializer.save()
        return Response(AdmissionSubjectSerializer(obj, context={'request': request}).data)

    @swagger_auto_schema(
        operation_summary="Delete subject",
        responses={200: openapi.Response(description="Deleted")},
        tags=['Admission - Subjects'],
    )
    def delete(self, request, *args, **kwargs):
        obj = self.get_object()
        name = obj.subject_name_uz or obj.subject_name_ru or ''
        obj.delete()
        return Response(
            {'id': obj.id, 'subject_name': name, 'detail': "Subject deleted successfully."},
            status=status.HTTP_200_OK,
        )


# ─────────────────────────────────────────────────────────────────────────────
# AdmissionDocument
# ─────────────────────────────────────────────────────────────────────────────

DOCUMENT_WRITE_PARAMS = [
    openapi.Parameter('document_name_uz', openapi.IN_FORM, type=openapi.TYPE_STRING, required=True, description="Document name (UZ)"),
    openapi.Parameter('document_name_ru', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="Document name (RU)"),
    openapi.Parameter('note_uz', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="Note (UZ)"),
    openapi.Parameter('note_ru', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="Note (RU)"),
    openapi.Parameter('document_file', openapi.IN_FORM, type=openapi.TYPE_FILE, required=False, description="File"),
    openapi.Parameter('is_required', openapi.IN_FORM, type=openapi.TYPE_BOOLEAN, required=False, default=True),
    openapi.Parameter('sort_order', openapi.IN_FORM, type=openapi.TYPE_INTEGER, required=False, default=0),
]


class AdmissionDocumentListCreateView(generics.ListCreateAPIView):
    """Documents list and create."""
    permission_classes = [IsAdminOrReadOnly]
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_required']
    search_fields = ['document_name_uz', 'document_name_ru', 'note_uz', 'note_ru']
    ordering_fields = ['sort_order', 'document_name_uz']
    ordering = ['sort_order']

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return AdmissionDocument.objects.none()
        return AdmissionDocument.objects.all()

    def get_serializer_class(self):
        if getattr(self, 'swagger_fake_view', False):
            return AdmissionDocumentSerializer
        return AdmissionDocumentWriteSerializer if self.request.method == 'POST' else AdmissionDocumentSerializer

    @swagger_auto_schema(
        operation_summary="Required documents list",
        operation_description=(
            "Required documents for admission.\n\n"
            "- `?is_active=true|false` (for admin)\n"
            "- `?search=...` — search by name/description\n"
            "- `?lang=uz|ru` — show only that language"
        ),
        manual_parameters=[LANG_PARAM],
        responses={200: AdmissionDocumentSerializer(many=True)},
        tags=['Admission - Documents'],
    )
    def get(self, request, *args, **kwargs):
        lang = request.query_params.get('lang')
        qs = self.filter_queryset(self.get_queryset())
        data = AdmissionDocumentSerializer(qs, many=True, context={'request': request}).data
        return Response(apply_lang_filter(list(data), lang))

    @swagger_auto_schema(
        operation_summary="Create new document",
        operation_description="Admin only. Sent via **`multipart/form-data`**.",
        manual_parameters=DOCUMENT_WRITE_PARAMS,
        consumes=['multipart/form-data'],
        responses={
            201: AdmissionDocumentSerializer,
            400: openapi.Response(description="Validation error"),
        },
        tags=['Admission - Documents'],
    )
    def post(self, request, *args, **kwargs):
        serializer = AdmissionDocumentWriteSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        obj = serializer.save()
        return Response(
            AdmissionDocumentSerializer(obj, context={'request': request}).data,
            status=status.HTTP_201_CREATED,
        )


class AdmissionDocumentDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Single document — view, edit, delete."""
    permission_classes = [IsAdminOrReadOnly]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return AdmissionDocument.objects.none()
        return AdmissionDocument.objects.all()

    def get_serializer_class(self):
        if getattr(self, 'swagger_fake_view', False):
            return AdmissionDocumentSerializer
        if self.request.method in ('PUT', 'PATCH'):
            return AdmissionDocumentWriteSerializer
        return AdmissionDocumentSerializer

    @swagger_auto_schema(
        operation_summary="Document detail",
        manual_parameters=[LANG_PARAM],
        responses={200: AdmissionDocumentSerializer, 404: openapi.Response(description="Not found")},
        tags=['Admission - Documents'],
    )
    def get(self, request, *args, **kwargs):
        obj = self.get_object()
        lang = request.query_params.get('lang')
        data = AdmissionDocumentSerializer(obj, context={'request': request}).data
        return Response(apply_lang_filter(data, lang))

    @swagger_auto_schema(
        operation_summary="Update document completely",
        operation_description="Admin only. Sent via **`multipart/form-data`**.",
        manual_parameters=DOCUMENT_WRITE_PARAMS,
        consumes=['multipart/form-data'],
        responses={200: AdmissionDocumentSerializer, 400: openapi.Response(description="Validation error")},
        tags=['Admission - Documents'],
    )
    def put(self, request, *args, **kwargs):
        obj = self.get_object()
        serializer = AdmissionDocumentWriteSerializer(obj, data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        obj = serializer.save()
        return Response(AdmissionDocumentSerializer(obj, context={'request': request}).data)

    @swagger_auto_schema(
        operation_summary="Update document partially",
        operation_description="Admin only. Only modified fields. **`multipart/form-data`**.",
        manual_parameters=DOCUMENT_WRITE_PARAMS,
        consumes=['multipart/form-data'],
        responses={200: AdmissionDocumentSerializer, 400: openapi.Response(description="Validation error")},
        tags=['Admission - Documents'],
    )
    def patch(self, request, *args, **kwargs):
        obj = self.get_object()
        serializer = AdmissionDocumentWriteSerializer(obj, data=request.data, partial=True, context={'request': request})
        serializer.is_valid(raise_exception=True)
        obj = serializer.save()
        return Response(AdmissionDocumentSerializer(obj, context={'request': request}).data)

    @swagger_auto_schema(
        operation_summary="Delete document",
        responses={200: openapi.Response(description="Deleted")},
        tags=['Admission - Documents'],
    )
    def delete(self, request, *args, **kwargs):
        obj = self.get_object()
        name = obj.document_name_uz or obj.document_name_ru or ''
        obj.delete()
        return Response(
            {'id': obj.id, 'document_name': name, 'detail': "Document deleted successfully."},
            status=status.HTTP_200_OK,
        )


# ─────────────────────────────────────────────────────────────────────────────
# FAQ
# ─────────────────────────────────────────────────────────────────────────────

FAQ_WRITE_PARAMS = [
    openapi.Parameter('question_uz', openapi.IN_FORM, type=openapi.TYPE_STRING, required=True, description="Question (UZ)"),
    openapi.Parameter('question_ru', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="Question (RU)"),
    openapi.Parameter('answer_uz', openapi.IN_FORM, type=openapi.TYPE_STRING, required=True, description="Answer (UZ)"),
    openapi.Parameter('answer_ru', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="Answer (RU)"),
    openapi.Parameter('category', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="Category (admission, general, etc.)"),
    openapi.Parameter('sort_order', openapi.IN_FORM, type=openapi.TYPE_INTEGER, required=False, default=0),
    openapi.Parameter('is_active', openapi.IN_FORM, type=openapi.TYPE_BOOLEAN, required=False, default=True),
]


class FAQListCreateView(generics.ListCreateAPIView):
    """FAQ list and create."""
    permission_classes = [IsAdminOrReadOnly]
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_active', 'category']
    search_fields = ['question_uz', 'question_ru', 'answer_uz', 'answer_ru']
    ordering_fields = ['sort_order', 'created_at']
    ordering = ['sort_order']

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return FAQ.objects.none()
        qs = FAQ.objects.all()
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
            return FAQSerializer
        return FAQWriteSerializer if self.request.method == 'POST' else FAQSerializer

    @swagger_auto_schema(
        operation_summary="FAQ list",
        operation_description=(
            "Frequently asked questions.\n\n"
            "- `?category=...` — filter by category\n"
            "- `?is_active=true|false` (for admin)\n"
            "- `?search=...` — search by question/answer\n"
            "- `?lang=uz|ru` — show only that language"
        ),
        manual_parameters=[LANG_PARAM],
        responses={200: FAQSerializer(many=True)},
        tags=['Admission - FAQ'],
    )
    def get(self, request, *args, **kwargs):
        lang = request.query_params.get('lang')
        qs = self.filter_queryset(self.get_queryset())
        data = FAQSerializer(qs, many=True, context={'request': request}).data
        return Response(apply_lang_filter(list(data), lang))

    @swagger_auto_schema(
        operation_summary="Create new FAQ",
        operation_description="Admin only. Sent via **`multipart/form-data`**.",
        manual_parameters=FAQ_WRITE_PARAMS,
        consumes=['multipart/form-data'],
        responses={
            201: FAQSerializer,
            400: openapi.Response(description="Validation error"),
        },
        tags=['Admission - FAQ'],
    )
    def post(self, request, *args, **kwargs):
        serializer = FAQWriteSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        obj = serializer.save()
        return Response(
            FAQSerializer(obj, context={'request': request}).data,
            status=status.HTTP_201_CREATED,
        )


class FAQFeaturedView(generics.ListAPIView):
    """Featured FAQs — shown on the main page."""
    permission_classes = [AllowAny]
    serializer_class = FAQSerializer
    filter_backends = [filters.OrderingFilter]
    ordering = ['sort_order']

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return FAQ.objects.none()
        return FAQ.objects.filter(is_featured=True, is_active=True)

    @swagger_auto_schema(
        operation_summary="Featured FAQs",
        operation_description=(
            "Featured (front-page) FAQs.\n\n"
            "- `?lang=uz|ru` — show only that language"
        ),
        manual_parameters=[LANG_PARAM],
        responses={200: FAQSerializer(many=True)},
        tags=['Admission - FAQ'],
    )
    def get(self, request, *args, **kwargs):
        lang = request.query_params.get('lang')
        qs = self.filter_queryset(self.get_queryset())
        data = FAQSerializer(qs, many=True, context={'request': request}).data
        return Response(apply_lang_filter(list(data), lang))


class FAQDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Single FAQ — view, edit, delete."""
    permission_classes = [IsAdminOrReadOnly]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return FAQ.objects.none()
        return FAQ.objects.all()

    def get_serializer_class(self):
        if getattr(self, 'swagger_fake_view', False):
            return FAQSerializer
        if self.request.method in ('PUT', 'PATCH'):
            return FAQWriteSerializer
        return FAQSerializer

    @swagger_auto_schema(
        operation_summary="FAQ detail",
        manual_parameters=[LANG_PARAM],
        responses={200: FAQSerializer, 404: openapi.Response(description="Not found")},
        tags=['Admission - FAQ'],
    )
    def get(self, request, *args, **kwargs):
        obj = self.get_object()
        lang = request.query_params.get('lang')
        data = FAQSerializer(obj, context={'request': request}).data
        return Response(apply_lang_filter(data, lang))

    @swagger_auto_schema(
        operation_summary="Update FAQ completely",
        operation_description="Admin only. Sent via **`multipart/form-data`**.",
        manual_parameters=FAQ_WRITE_PARAMS,
        consumes=['multipart/form-data'],
        responses={200: FAQSerializer, 400: openapi.Response(description="Validation error")},
        tags=['Admission - FAQ'],
    )
    def put(self, request, *args, **kwargs):
        obj = self.get_object()
        serializer = FAQWriteSerializer(obj, data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        obj = serializer.save()
        return Response(FAQSerializer(obj, context={'request': request}).data)

    @swagger_auto_schema(
        operation_summary="Update FAQ partially",
        operation_description="Admin only. Only modified fields. **`multipart/form-data`**.",
        manual_parameters=FAQ_WRITE_PARAMS,
        consumes=['multipart/form-data'],
        responses={200: FAQSerializer, 400: openapi.Response(description="Validation error")},
        tags=['Admission - FAQ'],
    )
    def patch(self, request, *args, **kwargs):
        obj = self.get_object()
        serializer = FAQWriteSerializer(obj, data=request.data, partial=True, context={'request': request})
        serializer.is_valid(raise_exception=True)
        obj = serializer.save()
        return Response(FAQSerializer(obj, context={'request': request}).data)

    @swagger_auto_schema(
        operation_summary="Delete FAQ",
        responses={200: openapi.Response(description="Deleted")},
        tags=['Admission - FAQ'],
    )
    def delete(self, request, *args, **kwargs):
        obj = self.get_object()
        q = obj.question_uz or obj.question_ru or ''
        obj.delete()
        return Response(
            {'id': obj.id, 'question': q[:80], 'detail': "FAQ deleted successfully."},
            status=status.HTTP_200_OK,
        )


# ─────────────────────────────────────────────────────────────────────────────
# DarsJadvali — Class Schedule
# ─────────────────────────────────────────────────────────────────────────────

DARS_WRITE_PARAMS = [
    openapi.Parameter('title_uz', openapi.IN_FORM, type=openapi.TYPE_STRING, required=True, description="Title (UZ)"),
    openapi.Parameter('title_ru', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="Title (RU)"),
    openapi.Parameter('file', openapi.IN_FORM, type=openapi.TYPE_FILE, required=True, description="Schedule file (PDF, DOCX, XLSX)"),
    openapi.Parameter('is_active', openapi.IN_FORM, type=openapi.TYPE_BOOLEAN, required=False, default=True),
    openapi.Parameter('sort_order', openapi.IN_FORM, type=openapi.TYPE_INTEGER, required=False, default=0),
]


class DarsJadvaliListCreateView(generics.ListCreateAPIView):
    """Class schedules list and create."""
    permission_classes = [IsAdminOrReadOnly]
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_active']
    search_fields = ['title_uz', 'title_ru']
    ordering_fields = ['sort_order', 'created_at']
    ordering = ['sort_order', '-created_at']

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return DarsJadvali.objects.none()
        qs = DarsJadvali.objects.all()
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
            return DarsJadvaliSerializer
        return DarsJadvaliWriteSerializer if self.request.method == 'POST' else DarsJadvaliSerializer

    @swagger_auto_schema(
        operation_summary="Class schedules list",
        operation_description=(
            "Class schedules list.\n\n"
            "- `?is_active=true|false` (for admin)\n"
            "- `?lang=uz|ru`"
        ),
        manual_parameters=[LANG_PARAM],
        responses={200: DarsJadvaliSerializer(many=True)},
        tags=['Admission - Schedule'],
    )
    def get(self, request, *args, **kwargs):
        lang = request.query_params.get('lang')
        qs = self.filter_queryset(self.get_queryset())
        data = DarsJadvaliSerializer(qs, many=True, context={'request': request}).data
        return Response(apply_lang_filter(list(data), lang))

    @swagger_auto_schema(
        operation_summary="Create new schedule",
        operation_description="Admin only. Sent via **`multipart/form-data`**.",
        manual_parameters=DARS_WRITE_PARAMS,
        consumes=['multipart/form-data'],
        responses={
            201: DarsJadvaliSerializer,
            400: openapi.Response(description="Validation error"),
        },
        tags=['Admission - Schedule'],
    )
    def post(self, request, *args, **kwargs):
        serializer = DarsJadvaliWriteSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        obj = serializer.save()
        return Response(
            DarsJadvaliSerializer(obj, context={'request': request}).data,
            status=status.HTTP_201_CREATED,
        )


class DarsJadvaliDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Single schedule — view, edit, delete."""
    permission_classes = [IsAdminOrReadOnly]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return DarsJadvali.objects.none()
        return DarsJadvali.objects.all()

    def get_serializer_class(self):
        if getattr(self, 'swagger_fake_view', False):
            return DarsJadvaliSerializer
        if self.request.method in ('PUT', 'PATCH'):
            return DarsJadvaliWriteSerializer
        return DarsJadvaliSerializer

    @swagger_auto_schema(
        operation_summary="Schedule detail",
        manual_parameters=[LANG_PARAM],
        responses={200: DarsJadvaliSerializer, 404: openapi.Response(description="Not found")},
        tags=['Admission - Schedule'],
    )
    def get(self, request, *args, **kwargs):
        obj = self.get_object()
        lang = request.query_params.get('lang')
        data = DarsJadvaliSerializer(obj, context={'request': request}).data
        return Response(apply_lang_filter(data, lang))

    @swagger_auto_schema(
        operation_summary="Update schedule completely",
        operation_description="Admin only. Sent via **`multipart/form-data`**.",
        manual_parameters=DARS_WRITE_PARAMS,
        consumes=['multipart/form-data'],
        responses={200: DarsJadvaliSerializer, 400: openapi.Response(description="Validation error")},
        tags=['Admission - Schedule'],
    )
    def put(self, request, *args, **kwargs):
        obj = self.get_object()
        serializer = DarsJadvaliWriteSerializer(obj, data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        obj = serializer.save()
        return Response(DarsJadvaliSerializer(obj, context={'request': request}).data)

    @swagger_auto_schema(
        operation_summary="Update schedule partially",
        operation_description="Admin only. Only modified fields. **`multipart/form-data`**.",
        manual_parameters=DARS_WRITE_PARAMS,
        consumes=['multipart/form-data'],
        responses={200: DarsJadvaliSerializer, 400: openapi.Response(description="Validation error")},
        tags=['Admission - Schedule'],
    )
    def patch(self, request, *args, **kwargs):
        obj = self.get_object()
        serializer = DarsJadvaliWriteSerializer(obj, data=request.data, partial=True, context={'request': request})
        serializer.is_valid(raise_exception=True)
        obj = serializer.save()
        return Response(DarsJadvaliSerializer(obj, context={'request': request}).data)

    @swagger_auto_schema(
        operation_summary="Delete schedule",
        responses={200: openapi.Response(description="Deleted")},
        tags=['Admission - Schedule'],
    )
    def delete(self, request, *args, **kwargs):
        obj = self.get_object()
        title = obj.title_uz or obj.title_ru or ''
        obj.delete()
        return Response(
            {'id': obj.id, 'title': title, 'detail': "Schedule deleted successfully."},
            status=status.HTTP_200_OK,
        )