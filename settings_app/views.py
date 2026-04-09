from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from accounts.permissions import IsAdminUser
from .models import SiteSettings
from .serializers import SiteSettingsSerializer, SiteSettingsWriteSerializer, apply_lang_filter

# ─── Swagger parametrlar ─────────────────────────────────────────────────────

LANG_PARAM = openapi.Parameter(
    'lang', openapi.IN_QUERY,
    description="Javob tilini filtrlash: uz | uz_cyrl | ru | en",
    type=openapi.TYPE_STRING,
    enum=['uz', 'uz_cyrl', 'ru', 'en'],
    required=False,
)


class SiteSettingsAPIView(APIView):
    """
    GET   — sayt sozlamalarini olish (hamma uchun ochiq)
    POST  — sozlamalarni yaratish (faqat admin, bir marta)
    PUT   — to'liq yangilash (faqat admin)
    PATCH — qisman yangilash (faqat admin)
    """
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_permissions(self):
        if self.request.method == 'GET':
            return [AllowAny()]
        return [IsAdminUser()]

    def _get_instance(self):
        return SiteSettings.get_instance()

    @swagger_auto_schema(
        operation_summary="Sayt sozlamalarini olish",
        operation_description=(
            "Sayt haqida umumiy ma'lumotlar: nomi, manzil, aloqa, logo, ijtimoiy tarmoqlar.\n\n"
            "- `?lang=uz|ru|en|uz_cyrl` — faqat o'sha tildagi tarjima"
        ),
        manual_parameters=[LANG_PARAM],
        responses={
            200: SiteSettingsSerializer,
            404: openapi.Response(description="Sozlamalar hali yaratilmagan"),
        },
        tags=["Settings"],
    )
    def get(self, request):
        instance = self._get_instance()
        if not instance:
            return Response(
                {'detail': "Sayt sozlamalari hali yaratilmagan."},
                status=status.HTTP_404_NOT_FOUND,
            )
        lang = request.query_params.get('lang')
        data = SiteSettingsSerializer(instance, context={'request': request}).data
        return Response(apply_lang_filter(data, lang))

    @swagger_auto_schema(
        operation_summary="Sayt sozlamalarini yaratish",
        operation_description=(
            "Faqat admin. Faqat bir marta yaratiladi. **`multipart/form-data`** orqali yuboriladi.\n\n"
            "Kamida bitta tilda `short_name_*` va `full_name_*` to'ldirilishi shart."
        ),
        manual_parameters=[
            openapi.Parameter('short_name_uz', openapi.IN_FORM, type=openapi.TYPE_STRING, required=True, description="Qisqa nomi (UZ)"),
            openapi.Parameter('short_name_ru', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="Qisqa nomi (RU)"),
            openapi.Parameter('short_name_en', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="Qisqa nomi (EN)"),
            openapi.Parameter('full_name_uz', openapi.IN_FORM, type=openapi.TYPE_STRING, required=True, description="To'liq nomi (UZ)"),
            openapi.Parameter('full_name_ru', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="To'liq nomi (RU)"),
            openapi.Parameter('full_name_en', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="To'liq nomi (EN)"),
            openapi.Parameter('address_uz', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="Manzil (UZ)"),
            openapi.Parameter('address_ru', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="Manzil (RU)"),
            openapi.Parameter('established_year', openapi.IN_FORM, type=openapi.TYPE_INTEGER, required=False, description="Tashkil etilgan yili"),
            openapi.Parameter('phone', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False),
            openapi.Parameter('email', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False),
            openapi.Parameter('website', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False),
            openapi.Parameter('logo', openapi.IN_FORM, type=openapi.TYPE_FILE, required=False, description="Logo rasmi"),
            openapi.Parameter('telegram', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False),
            openapi.Parameter('instagram', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False),
            openapi.Parameter('facebook', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False),
            openapi.Parameter('youtube', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False),
        ],
        consumes=['multipart/form-data'],
        responses={
            201: SiteSettingsSerializer,
            400: openapi.Response(description="Validatsiya xatosi yoki sozlamalar allaqachon mavjud"),
            403: openapi.Response(description="Ruxsat yo'q"),
        },
        tags=["Settings"],
    )
    def post(self, request):
        if self._get_instance():
            return Response(
                {'detail': "Sozlamalar allaqachon mavjud. Yangilash uchun PATCH ishlatilsin."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer = SiteSettingsWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        return Response(
            SiteSettingsSerializer(instance, context={'request': request}).data,
            status=status.HTTP_201_CREATED,
        )

    @swagger_auto_schema(
        operation_summary="Sozlamalarni to'liq yangilash",
        operation_description="Faqat admin. **`multipart/form-data`** orqali yuboriladi.",
        manual_parameters=[
            openapi.Parameter('short_name_uz', openapi.IN_FORM, type=openapi.TYPE_STRING, required=True, description="Qisqa nomi (UZ)"),
            openapi.Parameter('short_name_ru', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="Qisqa nomi (RU)"),
            openapi.Parameter('full_name_uz', openapi.IN_FORM, type=openapi.TYPE_STRING, required=True, description="To'liq nomi (UZ)"),
            openapi.Parameter('full_name_ru', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="To'liq nomi (RU)"),
            openapi.Parameter('address_uz', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="Manzil (UZ)"),
            openapi.Parameter('address_ru', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="Manzil (RU)"),
            openapi.Parameter('established_year', openapi.IN_FORM, type=openapi.TYPE_INTEGER, required=False),
            openapi.Parameter('phone', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False),
            openapi.Parameter('email', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False),
            openapi.Parameter('website', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False),
            openapi.Parameter('logo', openapi.IN_FORM, type=openapi.TYPE_FILE, required=False, description="Logo rasmi"),
            openapi.Parameter('telegram', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False),
            openapi.Parameter('instagram', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False),
        ],
        consumes=['multipart/form-data'],
        responses={
            200: SiteSettingsSerializer,
            400: openapi.Response(description="Validatsiya xatosi"),
            404: openapi.Response(description="Sozlamalar topilmadi"),
        },
        tags=["Settings"],
    )
    def put(self, request):
        instance = self._get_instance()
        if not instance:
            return Response(
                {'detail': "Sozlamalar topilmadi. Avval POST bilan yarating."},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = SiteSettingsWriteSerializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        return Response(SiteSettingsSerializer(instance, context={'request': request}).data)

    @swagger_auto_schema(
        operation_summary="Sozlamalarni qisman yangilash",
        operation_description="Faqat admin. Faqat o'zgartirilishi kerak bo'lgan maydonlar. **`multipart/form-data`**.",
        manual_parameters=[
            openapi.Parameter('short_name_uz', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="Qisqa nomi (UZ)"),
            openapi.Parameter('short_name_ru', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="Qisqa nomi (RU)"),
            openapi.Parameter('full_name_uz', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="To'liq nomi (UZ)"),
            openapi.Parameter('full_name_ru', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="To'liq nomi (RU)"),
            openapi.Parameter('address_uz', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="Manzil (UZ)"),
            openapi.Parameter('established_year', openapi.IN_FORM, type=openapi.TYPE_INTEGER, required=False),
            openapi.Parameter('phone', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False),
            openapi.Parameter('email', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False),
            openapi.Parameter('website', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False),
            openapi.Parameter('logo', openapi.IN_FORM, type=openapi.TYPE_FILE, required=False, description="Logo rasmi"),
            openapi.Parameter('telegram', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False),
            openapi.Parameter('instagram', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False),
            openapi.Parameter('facebook', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False),
            openapi.Parameter('youtube', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False),
        ],
        consumes=['multipart/form-data'],
        responses={
            200: SiteSettingsSerializer,
            400: openapi.Response(description="Validatsiya xatosi"),
            404: openapi.Response(description="Sozlamalar topilmadi"),
        },
        tags=["Settings"],
    )
    def patch(self, request):
        instance = self._get_instance()
        if not instance:
            return Response(
                {'detail': "Sozlamalar topilmadi. Avval POST bilan yarating."},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = SiteSettingsWriteSerializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        return Response(SiteSettingsSerializer(instance, context={'request': request}).data)
