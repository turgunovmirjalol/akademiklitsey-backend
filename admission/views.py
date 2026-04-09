"""
Admission app views.

Barcha write endpointlar multipart/form-data qabul qiladi.
Har bir til maydoni alohida flat field sifatida yuboriladi.
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
from .models import AdmissionInfo, AdmissionSubject, AdmissionDocument, FAQ
from .serializers import (
    AdmissionInfoSerializer,
    AdmissionInfoWriteSerializer,
    AdmissionSubjectSerializer,
    AdmissionSubjectWriteSerializer,
    AdmissionDocumentSerializer,
    AdmissionDocumentWriteSerializer,
    FAQSerializer,
    FAQWriteSerializer,
)

# ─── Swagger umumiy parametrlar ──────────────────────────────────────────────

LANG_PARAM = openapi.Parameter(
    'lang', openapi.IN_QUERY,
    description="Javob tilini filtrlash: uz | uz_cyrl | ru | en (ixtiyoriy, ko'rsatilmasa barcha tillar)",
    type=openapi.TYPE_STRING,
    enum=['uz', 'uz_cyrl', 'ru', 'en'],
    required=False,
)


def filter_by_lang(data: dict, lang: str) -> dict:
    """
    Agar ?lang= berilgan bo'lsa, translations ichidan faqat o'sha tilni qaytaradi.
    """
    if not lang or lang not in ('uz', 'uz_cyrl', 'ru', 'en'):
        return data
    if isinstance(data, dict) and 'translations' in data:
        t = data.get('translations') or {}
        data['translations'] = {lang: t.get(lang, {})} if t else {}
    return data


def apply_lang_filter(serializer_data, lang: str):
    """List yoki detail response uchun til filtrini qo'llaydi."""
    if not lang:
        return serializer_data
    if isinstance(serializer_data, list):
        return [filter_by_lang(item, lang) for item in serializer_data]
    return filter_by_lang(serializer_data, lang)


# ─────────────────────────────────────────────────────────────────────────────
# AdmissionInfo
# ─────────────────────────────────────────────────────────────────────────────

class AdmissionCurrentView(APIView):
    """
    Joriy faol qabul ma'lumotlari + fanlar + hujjatlar.
    GET  — hamma uchun ochiq
    POST — faqat admin (yangi qabul yaratish)
    PUT  — faqat admin (joriy qabulni yangilash)
    """
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_permissions(self):
        if self.request.method == 'GET':
            return [AllowAny()]
        return [IsAdminOrReadOnly()]

    def _get_active(self):
        return AdmissionInfo.objects.filter(is_active=True).first()

    @swagger_auto_schema(
        operation_summary="Joriy qabul ma'lumotlari",
        operation_description=(
            "Faol qabul ma'lumotlari, imtihon fanlari va talab qilinadigan hujjatlarni qaytaradi.\n\n"
            "?lang=uz — faqat o'zbek tilida\n"
            "?lang=ru — faqat rus tilida"
        ),
        manual_parameters=[LANG_PARAM],
        responses={
            200: openapi.Response(
                description="Muvaffaqiyatli",
                examples={
                    "application/json": {
                        "admission_info": {"id": 1, "academic_year": "2026-2027"},
                        "subjects": [],
                        "documents": [],
                    }
                }
            ),
            404: openapi.Response(description="Faol qabul topilmadi"),
        },
        tags=['Admission'],
    )
    def get(self, request):
        obj = self._get_active()
        if not obj:
            return Response(
                {"detail": "Joriy qabul ma'lumotlari topilmadi."},
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
        operation_summary="Yangi qabul ma'lumoti yaratish",
        operation_description="Faqat admin. Faol qabul allaqachon mavjud bo'lsa xato qaytaradi.",
        request_body=AdmissionInfoWriteSerializer,
        responses={
            201: AdmissionInfoSerializer,
            400: openapi.Response(description="Validatsiya xatosi yoki faol qabul allaqachon mavjud"),
        },
        tags=['Admission'],
    )
    def post(self, request):
        if self._get_active():
            return Response(
                {"detail": "Faol qabul ma'lumoti allaqachon mavjud. Yangilash uchun PUT ishlatilsin."},
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
        operation_summary="Joriy qabul ma'lumotini yangilash",
        operation_description="Faqat admin. Partial update qo'llab-quvvatlanadi.",
        request_body=AdmissionInfoWriteSerializer,
        responses={
            200: AdmissionInfoSerializer,
            404: openapi.Response(description="Faol qabul topilmadi"),
        },
        tags=['Admission'],
    )
    def put(self, request):
        obj = self._get_active()
        if not obj:
            return Response(
                {"detail": "Joriy qabul ma'lumotlari topilmadi."},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = AdmissionInfoWriteSerializer(obj, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        obj = serializer.save()
        return Response(AdmissionInfoSerializer(obj, context={'request': request}).data)


class AdmissionHistoryView(generics.ListAPIView):
    """O'tgan yillar qabul tarixi (nofaol yozuvlar)."""
    permission_classes = [AllowAny]
    serializer_class = AdmissionInfoSerializer
    filter_backends = [filters.OrderingFilter]
    ordering = ['-academic_year']

    def get_queryset(self):
        return AdmissionInfo.objects.filter(is_active=False)

    @swagger_auto_schema(
        operation_summary="Qabul tarixi",
        operation_description="O'tgan yillar qabul ma'lumotlari (nofaol yozuvlar).",
        tags=['Admission'],
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


# ─────────────────────────────────────────────────────────────────────────────
# AdmissionSubject
# ─────────────────────────────────────────────────────────────────────────────

class AdmissionSubjectsView(generics.ListCreateAPIView):
    """Imtihon fanlari ro'yxati va yaratish."""
    permission_classes = [IsAdminOrReadOnly]
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    filter_backends = [filters.OrderingFilter]
    ordering = ['sort_order']

    def get_queryset(self):
        return AdmissionSubject.objects.all()

    def get_serializer_class(self):
        if getattr(self, 'swagger_fake_view', False):
            return AdmissionSubjectSerializer
        return AdmissionSubjectWriteSerializer if self.request.method == 'POST' else AdmissionSubjectSerializer

    @swagger_auto_schema(
        operation_summary="Imtihon fanlari ro'yxati",
        manual_parameters=[LANG_PARAM],
        responses={200: AdmissionSubjectSerializer(many=True)},
        tags=['Admission - Subjects'],
    )
    def get(self, request, *args, **kwargs):
        lang = request.query_params.get('lang')
        qs = self.get_queryset()
        data = AdmissionSubjectSerializer(qs, many=True, context={'request': request}).data
        return Response(apply_lang_filter(data, lang))

    @swagger_auto_schema(
        operation_summary="Yangi imtihon fani yaratish",
        operation_description=(
            "Har bir til uchun maydonlar alohida yuboriladi.\n\n"
            "Kamida bitta tilda `subject_name_*` to'ldirilishi shart."
        ),
        manual_parameters=[
            openapi.Parameter('subject_name_uz', openapi.IN_FORM, type=openapi.TYPE_STRING, required=True, description="Fan nomi (UZ)"),
            openapi.Parameter('subject_name_ru', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="Fan nomi (RU)"),
            openapi.Parameter('subject_name_en', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="Fan nomi (EN)"),
            openapi.Parameter('subject_name_uz_cyrl', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="Fan nomi (UZ Kirill)"),
            openapi.Parameter('description_uz', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="Tavsif (UZ)"),
            openapi.Parameter('description_ru', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="Tavsif (RU)"),
            openapi.Parameter('subject_type', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, enum=['test', 'essay', 'interview'], default='test'),
            openapi.Parameter('max_score', openapi.IN_FORM, type=openapi.TYPE_INTEGER, required=True, description="Maksimal ball"),
            openapi.Parameter('sort_order', openapi.IN_FORM, type=openapi.TYPE_INTEGER, required=False, default=0),
        ],
        consumes=['multipart/form-data'],
        responses={
            201: AdmissionSubjectSerializer,
            400: openapi.Response(description="Validatsiya xatosi"),
        },
        tags=['Admission - Subjects'],
    )
    def post(self, request, *args, **kwargs):
        serializer = AdmissionSubjectWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        obj = serializer.save()
        return Response(
            AdmissionSubjectSerializer(obj, context={'request': request}).data,
            status=status.HTTP_201_CREATED,
        )


class AdmissionSubjectDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Bitta imtihon fani — ko'rish, tahrirlash, o'chirish."""
    permission_classes = [IsAdminOrReadOnly]
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    queryset = AdmissionSubject.objects.all()

    def get_serializer_class(self):
        if getattr(self, 'swagger_fake_view', False):
            return AdmissionSubjectSerializer
        if self.request.method in ('PUT', 'PATCH'):
            return AdmissionSubjectWriteSerializer
        return AdmissionSubjectSerializer

    @swagger_auto_schema(
        operation_summary="Imtihon fani detali",
        manual_parameters=[LANG_PARAM],
        responses={200: AdmissionSubjectSerializer},
        tags=['Admission - Subjects'],
    )
    def get(self, request, *args, **kwargs):
        obj = self.get_object()
        lang = request.query_params.get('lang')
        data = AdmissionSubjectSerializer(obj, context={'request': request}).data
        return Response(apply_lang_filter(data, lang))

    @swagger_auto_schema(
        operation_summary="Imtihon fanini to'liq yangilash",
        manual_parameters=[
            openapi.Parameter('subject_name_uz', openapi.IN_FORM, type=openapi.TYPE_STRING, required=True, description="Fan nomi (UZ)"),
            openapi.Parameter('subject_name_ru', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="Fan nomi (RU)"),
            openapi.Parameter('description_uz', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="Tavsif (UZ)"),
            openapi.Parameter('description_ru', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="Tavsif (RU)"),
            openapi.Parameter('subject_type', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, enum=['test', 'essay', 'interview']),
            openapi.Parameter('max_score', openapi.IN_FORM, type=openapi.TYPE_INTEGER, required=True),
            openapi.Parameter('sort_order', openapi.IN_FORM, type=openapi.TYPE_INTEGER, required=False),
        ],
        consumes=['multipart/form-data'],
        responses={200: AdmissionSubjectSerializer},
        tags=['Admission - Subjects'],
    )
    def put(self, request, *args, **kwargs):
        obj = self.get_object()
        serializer = AdmissionSubjectWriteSerializer(obj, data=request.data)
        serializer.is_valid(raise_exception=True)
        obj = serializer.save()
        return Response(AdmissionSubjectSerializer(obj, context={'request': request}).data)

    @swagger_auto_schema(
        operation_summary="Imtihon fanini qisman yangilash",
        manual_parameters=[
            openapi.Parameter('subject_name_uz', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="Fan nomi (UZ)"),
            openapi.Parameter('subject_name_ru', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="Fan nomi (RU)"),
            openapi.Parameter('description_uz', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="Tavsif (UZ)"),
            openapi.Parameter('subject_type', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, enum=['test', 'essay', 'interview']),
            openapi.Parameter('max_score', openapi.IN_FORM, type=openapi.TYPE_INTEGER, required=False),
            openapi.Parameter('sort_order', openapi.IN_FORM, type=openapi.TYPE_INTEGER, required=False),
        ],
        consumes=['multipart/form-data'],
        responses={200: AdmissionSubjectSerializer},
        tags=['Admission - Subjects'],
    )
    def patch(self, request, *args, **kwargs):
        obj = self.get_object()
        serializer = AdmissionSubjectWriteSerializer(obj, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        obj = serializer.save()
        return Response(AdmissionSubjectSerializer(obj, context={'request': request}).data)

    @swagger_auto_schema(
        operation_summary="Imtihon fanini o'chirish",
        responses={200: openapi.Response(description="O'chirildi")},
        tags=['Admission - Subjects'],
    )
    def delete(self, request, *args, **kwargs):
        obj = self.get_object()
        name = obj.subject_name_uz or obj.subject_name_ru or obj.subject_name_en or ''
        obj.delete()
        return Response(
            {'id': obj.id, 'subject_name': name, 'detail': "Fan muvaffaqiyatli o'chirildi."},
            status=status.HTTP_200_OK,
        )


# ─────────────────────────────────────────────────────────────────────────────
# AdmissionDocument
# ─────────────────────────────────────────────────────────────────────────────

class AdmissionDocumentsView(generics.ListCreateAPIView):
    """Talab qilinadigan hujjatlar ro'yxati va yaratish."""
    permission_classes = [IsAdminOrReadOnly]
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    filter_backends = [filters.OrderingFilter]
    ordering = ['sort_order']

    def get_queryset(self):
        return AdmissionDocument.objects.all()

    def get_serializer_class(self):
        if getattr(self, 'swagger_fake_view', False):
            return AdmissionDocumentSerializer
        return AdmissionDocumentWriteSerializer if self.request.method == 'POST' else AdmissionDocumentSerializer

    @swagger_auto_schema(
        operation_summary="Hujjatlar ro'yxati",
        manual_parameters=[LANG_PARAM],
        responses={200: AdmissionDocumentSerializer(many=True)},
        tags=['Admission - Documents'],
    )
    def get(self, request, *args, **kwargs):
        lang = request.query_params.get('lang')
        qs = self.get_queryset()
        data = AdmissionDocumentSerializer(qs, many=True, context={'request': request}).data
        return Response(apply_lang_filter(data, lang))

    @swagger_auto_schema(
        operation_summary="Yangi hujjat yaratish",
        operation_description=(
            "Har bir til uchun maydonlar alohida yuboriladi. **`multipart/form-data`** orqali yuboriladi.\n\n"
            "Kamida bitta tilda `document_name_*` to'ldirilishi shart.\n\n"
            "`document_file` — ixtiyoriy fayl (PDF, DOCX, JPG va h.k.)"
        ),
        manual_parameters=[
            openapi.Parameter('document_name_uz', openapi.IN_FORM, type=openapi.TYPE_STRING, required=True, description="Hujjat nomi (UZ)"),
            openapi.Parameter('document_name_ru', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="Hujjat nomi (RU)"),
            openapi.Parameter('document_name_en', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="Hujjat nomi (EN)"),
            openapi.Parameter('document_name_uz_cyrl', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="Hujjat nomi (UZ Kirill)"),
            openapi.Parameter('note_uz', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="Izoh (UZ)"),
            openapi.Parameter('note_ru', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="Izoh (RU)"),
            openapi.Parameter('note_en', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="Izoh (EN)"),
            openapi.Parameter('document_file', openapi.IN_FORM, type=openapi.TYPE_FILE, required=False, description="Hujjat fayli (PDF, DOCX, JPG va h.k.)"),
            openapi.Parameter('is_required', openapi.IN_FORM, type=openapi.TYPE_BOOLEAN, required=False, default=True, description="Majburiy hujjatmi"),
            openapi.Parameter('sort_order', openapi.IN_FORM, type=openapi.TYPE_INTEGER, required=False, default=0),
        ],
        consumes=['multipart/form-data'],
        responses={
            201: AdmissionDocumentSerializer,
            400: openapi.Response(description="Validatsiya xatosi"),
        },
        tags=['Admission - Documents'],
    )
    def post(self, request, *args, **kwargs):
        serializer = AdmissionDocumentWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        obj = serializer.save()
        return Response(
            AdmissionDocumentSerializer(obj, context={'request': request}).data,
            status=status.HTTP_201_CREATED,
        )


class AdmissionDocumentDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Bitta hujjat — ko'rish, tahrirlash, o'chirish."""
    permission_classes = [IsAdminOrReadOnly]
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    queryset = AdmissionDocument.objects.all()

    def get_serializer_class(self):
        if getattr(self, 'swagger_fake_view', False):
            return AdmissionDocumentSerializer
        if self.request.method in ('PUT', 'PATCH'):
            return AdmissionDocumentWriteSerializer
        return AdmissionDocumentSerializer

    @swagger_auto_schema(
        operation_summary="Hujjat detali",
        manual_parameters=[LANG_PARAM],
        responses={200: AdmissionDocumentSerializer},
        tags=['Admission - Documents'],
    )
    def get(self, request, *args, **kwargs):
        obj = self.get_object()
        lang = request.query_params.get('lang')
        data = AdmissionDocumentSerializer(obj, context={'request': request}).data
        return Response(apply_lang_filter(data, lang))

    @swagger_auto_schema(
        operation_summary="Hujjatni to'liq yangilash",
        operation_description="Faqat admin. **`multipart/form-data`** orqali yuboriladi.",
        manual_parameters=[
            openapi.Parameter('document_name_uz', openapi.IN_FORM, type=openapi.TYPE_STRING, required=True, description="Hujjat nomi (UZ)"),
            openapi.Parameter('document_name_ru', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="Hujjat nomi (RU)"),
            openapi.Parameter('document_name_en', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="Hujjat nomi (EN)"),
            openapi.Parameter('note_uz', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="Izoh (UZ)"),
            openapi.Parameter('note_ru', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="Izoh (RU)"),
            openapi.Parameter('document_file', openapi.IN_FORM, type=openapi.TYPE_FILE, required=False, description="Hujjat fayli (PDF, DOCX va h.k.)"),
            openapi.Parameter('is_required', openapi.IN_FORM, type=openapi.TYPE_BOOLEAN, required=False, default=True),
            openapi.Parameter('sort_order', openapi.IN_FORM, type=openapi.TYPE_INTEGER, required=False, default=0),
        ],
        consumes=['multipart/form-data'],
        responses={200: AdmissionDocumentSerializer},
        tags=['Admission - Documents'],
    )
    def put(self, request, *args, **kwargs):
        obj = self.get_object()
        serializer = AdmissionDocumentWriteSerializer(obj, data=request.data)
        serializer.is_valid(raise_exception=True)
        obj = serializer.save()
        return Response(AdmissionDocumentSerializer(obj, context={'request': request}).data)

    @swagger_auto_schema(
        operation_summary="Hujjatni qisman yangilash",
        operation_description="Faqat admin. Faqat o'zgartirilishi kerak bo'lgan maydonlar. **`multipart/form-data`**.",
        manual_parameters=[
            openapi.Parameter('document_name_uz', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="Hujjat nomi (UZ)"),
            openapi.Parameter('document_name_ru', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="Hujjat nomi (RU)"),
            openapi.Parameter('note_uz', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="Izoh (UZ)"),
            openapi.Parameter('document_file', openapi.IN_FORM, type=openapi.TYPE_FILE, required=False, description="Hujjat fayli (PDF, DOCX va h.k.)"),
            openapi.Parameter('is_required', openapi.IN_FORM, type=openapi.TYPE_BOOLEAN, required=False),
            openapi.Parameter('sort_order', openapi.IN_FORM, type=openapi.TYPE_INTEGER, required=False),
        ],
        consumes=['multipart/form-data'],
        responses={200: AdmissionDocumentSerializer},
        tags=['Admission - Documents'],
    )
    def patch(self, request, *args, **kwargs):
        obj = self.get_object()
        serializer = AdmissionDocumentWriteSerializer(obj, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        obj = serializer.save()
        return Response(AdmissionDocumentSerializer(obj, context={'request': request}).data)

    @swagger_auto_schema(
        operation_summary="Hujjatni o'chirish",
        responses={200: openapi.Response(description="O'chirildi")},
        tags=['Admission - Documents'],
    )
    def delete(self, request, *args, **kwargs):
        obj = self.get_object()
        name = obj.document_name_uz or obj.document_name_ru or obj.document_name_en or ''
        obj.delete()
        return Response(
            {'id': obj.id, 'document_name': name, 'detail': "Hujjat muvaffaqiyatli o'chirildi."},
            status=status.HTTP_200_OK,
        )


# ─────────────────────────────────────────────────────────────────────────────
# FAQ
# ─────────────────────────────────────────────────────────────────────────────

class FAQListView(generics.ListCreateAPIView):
    """FAQ ro'yxati va yaratish."""
    permission_classes = [IsAdminOrReadOnly]
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'is_active', 'is_featured']
    search_fields = [
        'question_uz', 'question_ru', 'question_en',
        'answer_uz', 'answer_ru', 'answer_en',
    ]
    ordering = ['sort_order']

    def get_queryset(self):
        return FAQ.objects.all()

    def get_serializer_class(self):
        if getattr(self, 'swagger_fake_view', False):
            return FAQSerializer
        return FAQWriteSerializer if self.request.method == 'POST' else FAQSerializer

    @swagger_auto_schema(
        operation_summary="FAQ ro'yxati",
        operation_description=(
            "Barcha FAQ lar. Filterlar:\n"
            "- `?category=admission|general|education|payment`\n"
            "- `?is_active=true|false`\n"
            "- `?is_featured=true|false`\n"
            "- `?search=...` — savol/javob bo'yicha qidirish\n"
            "- `?lang=uz|ru|en|uz_cyrl` — faqat o'sha tildagi tarjimani qaytarish"
        ),
        manual_parameters=[LANG_PARAM],
        responses={200: FAQSerializer(many=True)},
        tags=['FAQ'],
    )
    def get(self, request, *args, **kwargs):
        lang = request.query_params.get('lang')
        qs = self.filter_queryset(self.get_queryset())
        data = FAQSerializer(qs, many=True, context={'request': request}).data
        return Response(apply_lang_filter(data, lang))

    @swagger_auto_schema(
        operation_summary="Yangi FAQ yaratish",
        operation_description=(
            "Har bir til uchun savol va javob alohida maydonlarda yuboriladi.\n\n"
            "Kamida bitta tilda `question_*` va `answer_*` to'ldirilishi shart."
        ),
        manual_parameters=[
            openapi.Parameter('question_uz', openapi.IN_FORM, type=openapi.TYPE_STRING, required=True, description="Savol (UZ)"),
            openapi.Parameter('question_ru', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="Savol (RU)"),
            openapi.Parameter('question_en', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="Savol (EN)"),
            openapi.Parameter('question_uz_cyrl', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="Savol (UZ Kirill)"),
            openapi.Parameter('answer_uz', openapi.IN_FORM, type=openapi.TYPE_STRING, required=True, description="Javob (UZ)"),
            openapi.Parameter('answer_ru', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="Javob (RU)"),
            openapi.Parameter('answer_en', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="Javob (EN)"),
            openapi.Parameter('answer_uz_cyrl', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="Javob (UZ Kirill)"),
            openapi.Parameter('category', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, enum=['admission', 'general', 'education', 'payment'], default='general'),
            openapi.Parameter('is_featured', openapi.IN_FORM, type=openapi.TYPE_BOOLEAN, required=False, default=False),
            openapi.Parameter('is_active', openapi.IN_FORM, type=openapi.TYPE_BOOLEAN, required=False, default=True),
            openapi.Parameter('sort_order', openapi.IN_FORM, type=openapi.TYPE_INTEGER, required=False, default=0),
        ],
        consumes=['multipart/form-data'],
        responses={
            201: FAQSerializer,
            400: openapi.Response(description="Validatsiya xatosi"),
        },
        tags=['FAQ'],
    )
    def post(self, request, *args, **kwargs):
        serializer = FAQWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        obj = serializer.save()
        return Response(
            FAQSerializer(obj, context={'request': request}).data,
            status=status.HTTP_201_CREATED,
        )


class FAQFeaturedView(generics.ListAPIView):
    """Bosh sahifa uchun featured FAQ lar."""
    permission_classes = [AllowAny]
    serializer_class = FAQSerializer

    def get_queryset(self):
        return FAQ.objects.filter(is_featured=True, is_active=True).order_by('sort_order')

    @swagger_auto_schema(
        operation_summary="Featured FAQ lar",
        operation_description="Bosh sahifada ko'rsatiladigan FAQ lar (is_featured=True, is_active=True).",
        manual_parameters=[LANG_PARAM],
        responses={200: FAQSerializer(many=True)},
        tags=['FAQ'],
    )
    def get(self, request, *args, **kwargs):
        lang = request.query_params.get('lang')
        qs = self.get_queryset()
        data = FAQSerializer(qs, many=True, context={'request': request}).data
        return Response(apply_lang_filter(data, lang))


class FAQDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Bitta FAQ — ko'rish, tahrirlash, o'chirish."""
    permission_classes = [IsAdminOrReadOnly]
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    queryset = FAQ.objects.all()

    def get_serializer_class(self):
        if getattr(self, 'swagger_fake_view', False):
            return FAQSerializer
        if self.request.method in ('PUT', 'PATCH'):
            return FAQWriteSerializer
        return FAQSerializer

    @swagger_auto_schema(
        operation_summary="FAQ detali",
        manual_parameters=[LANG_PARAM],
        responses={200: FAQSerializer},
        tags=['FAQ'],
    )
    def get(self, request, *args, **kwargs):
        obj = self.get_object()
        lang = request.query_params.get('lang')
        data = FAQSerializer(obj, context={'request': request}).data
        return Response(apply_lang_filter(data, lang))

    @swagger_auto_schema(
        operation_summary="FAQ ni to'liq yangilash",
        manual_parameters=[
            openapi.Parameter('question_uz', openapi.IN_FORM, type=openapi.TYPE_STRING, required=True, description="Savol (UZ)"),
            openapi.Parameter('question_ru', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="Savol (RU)"),
            openapi.Parameter('answer_uz', openapi.IN_FORM, type=openapi.TYPE_STRING, required=True, description="Javob (UZ)"),
            openapi.Parameter('answer_ru', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="Javob (RU)"),
            openapi.Parameter('category', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, enum=['admission', 'general', 'education', 'payment']),
            openapi.Parameter('is_featured', openapi.IN_FORM, type=openapi.TYPE_BOOLEAN, required=False),
            openapi.Parameter('is_active', openapi.IN_FORM, type=openapi.TYPE_BOOLEAN, required=False),
            openapi.Parameter('sort_order', openapi.IN_FORM, type=openapi.TYPE_INTEGER, required=False),
        ],
        consumes=['multipart/form-data'],
        responses={200: FAQSerializer},
        tags=['FAQ'],
    )
    def put(self, request, *args, **kwargs):
        obj = self.get_object()
        serializer = FAQWriteSerializer(obj, data=request.data)
        serializer.is_valid(raise_exception=True)
        obj = serializer.save()
        return Response(FAQSerializer(obj, context={'request': request}).data)

    @swagger_auto_schema(
        operation_summary="FAQ ni qisman yangilash",
        manual_parameters=[
            openapi.Parameter('question_uz', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="Savol (UZ)"),
            openapi.Parameter('question_ru', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="Savol (RU)"),
            openapi.Parameter('answer_uz', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="Javob (UZ)"),
            openapi.Parameter('answer_ru', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="Javob (RU)"),
            openapi.Parameter('category', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, enum=['admission', 'general', 'education', 'payment']),
            openapi.Parameter('is_featured', openapi.IN_FORM, type=openapi.TYPE_BOOLEAN, required=False),
            openapi.Parameter('is_active', openapi.IN_FORM, type=openapi.TYPE_BOOLEAN, required=False),
            openapi.Parameter('sort_order', openapi.IN_FORM, type=openapi.TYPE_INTEGER, required=False),
        ],
        consumes=['multipart/form-data'],
        responses={200: FAQSerializer},
        tags=['FAQ'],
    )
    def patch(self, request, *args, **kwargs):
        obj = self.get_object()
        serializer = FAQWriteSerializer(obj, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        obj = serializer.save()
        return Response(FAQSerializer(obj, context={'request': request}).data)

    @swagger_auto_schema(
        operation_summary="FAQ ni o'chirish",
        responses={200: openapi.Response(description="O'chirildi")},
        tags=['FAQ'],
    )
    def delete(self, request, *args, **kwargs):
        obj = self.get_object()
        q = obj.question_uz or obj.question_ru or obj.question_en or ''
        obj.delete()
        return Response(
            {'id': obj.id, 'question': q[:80], 'detail': "FAQ muvaffaqiyatli o'chirildi."},
            status=status.HTTP_200_OK,
        )
