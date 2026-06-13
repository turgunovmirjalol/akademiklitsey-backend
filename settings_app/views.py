from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from accounts.permissions import IsAdminUser
from .models import SiteSettings, Slider
from .serializers import (
    SiteSettingsSerializer, SiteSettingsWriteSerializer, apply_lang_filter,
    SliderSerializer, SliderWriteSerializer,
)

# ─── Swagger uchun qayta ishlatiladigan parametrlar ──────────────────────────

LANG_PARAM = openapi.Parameter(
    'lang', openapi.IN_QUERY,
    description="Javob tilini filtrlash: uz | ru",
    type=openapi.TYPE_STRING,
    enum=['uz', 'ru'],
    required=False,
)

# Ko'p tillik maydonlar — POST/PUT/PATCH uchun
MULTILANG_PARAMS = [
    openapi.Parameter('short_name_uz',      openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="Qisqa nomi (O'zbek lotin)"),
    openapi.Parameter('short_name_ru',      openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="Qisqa nomi (Rus)"),
    openapi.Parameter('full_name_uz',       openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="To'liq nomi (O'zbek lotin)"),
    openapi.Parameter('full_name_ru',       openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="To'liq nomi (Rus)"),
    openapi.Parameter('address_uz',         openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="Manzil (O'zbek lotin)"),
    openapi.Parameter('address_ru',         openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="Manzil (Rus)"),
]

COMMON_PARAMS = [
    openapi.Parameter('established_year', openapi.IN_FORM, type=openapi.TYPE_INTEGER, required=False, description="Tashkil etilgan yili"),
    openapi.Parameter('phone',    openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="Telefon raqami"),
    openapi.Parameter('email',    openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="Elektron pochta"),
    openapi.Parameter('website',  openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="Veb-sayt URL"),
    openapi.Parameter('logo',     openapi.IN_FORM, type=openapi.TYPE_FILE,   required=False, description="Logo rasmi"),
    openapi.Parameter('telegram', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="Telegram URL"),
    openapi.Parameter('instagram',openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="Instagram URL"),
    openapi.Parameter('facebook', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="Facebook URL"),
    openapi.Parameter('youtube',  openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="YouTube URL"),
]

ALL_WRITE_PARAMS = MULTILANG_PARAMS + COMMON_PARAMS


class SiteSettingsAPIView(APIView):
    """
    GET   — sayt sozlamalarini olish (hamma uchun ochiq)
    PUT   — to'liq yangilash (faqat admin)
    PATCH — qisman yangilash (faqat admin)
    """
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_permissions(self):
        if self.request.method == 'GET':
            return [AllowAny()]
        return [IsAdminUser()]

    def _get_instance(self):
        instance = SiteSettings.get_instance()
        if not instance:
            instance = SiteSettings.objects.create(
                short_name_uz="Akademik Litsey",
                full_name_uz="Akademik Litsey",
                address_uz="Toshkent shahri",
                established_year=2000,
            )
        return instance

    @swagger_auto_schema(
        operation_summary="Sayt sozlamalarini olish",
        operation_description=(
            "Sayt haqida umumiy ma'lumotlar: nomi, manzil, aloqa, logo, ijtimoiy tarmoqlar.\n\n"
            "`?lang=uz|ru` — faqat o'sha tildagi tarjima qaytariladi."
        ),
        manual_parameters=[LANG_PARAM],
        responses={
            200: SiteSettingsSerializer,
        },
        tags=["Settings"],
    )
    def get(self, request):
        instance = self._get_instance()
        lang = request.query_params.get('lang')
        data = SiteSettingsSerializer(instance, context={'request': request}).data
        return Response(apply_lang_filter(data, lang))

    @swagger_auto_schema(
        operation_summary="Sozlamalarni to'liq yangilash",
        operation_description="Faqat admin. Barcha maydonlar yuborilishi kerak. **`multipart/form-data`**.",
        manual_parameters=ALL_WRITE_PARAMS,
        consumes=['multipart/form-data'],
        responses={
            200: SiteSettingsSerializer,
            400: openapi.Response(description="Validatsiya xatosi"),
            403: openapi.Response(description="Ruxsat yo'q"),
        },
        tags=["Settings"],
    )
    def put(self, request):
        instance = self._get_instance()
        serializer = SiteSettingsWriteSerializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        return Response(SiteSettingsSerializer(instance, context={'request': request}).data)

    @swagger_auto_schema(
        operation_summary="Sozlamalarni qisman yangilash",
        operation_description="Faqat admin. Faqat o'zgartirilishi kerak bo'lgan maydonlar. **`multipart/form-data`**.",
        manual_parameters=ALL_WRITE_PARAMS,
        consumes=['multipart/form-data'],
        responses={
            200: SiteSettingsSerializer,
            400: openapi.Response(description="Validatsiya xatosi"),
            403: openapi.Response(description="Ruxsat yo'q"),
        },
        tags=["Settings"],
    )
    def patch(self, request):
        instance = self._get_instance()
        serializer = SiteSettingsWriteSerializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        return Response(SiteSettingsSerializer(instance, context={'request': request}).data)


# ─── Slider ──────────────────────────────────────────────────────────────────

SLIDER_WRITE_PARAMS = [
    openapi.Parameter('image',          openapi.IN_FORM, type=openapi.TYPE_FILE,    required=False, description="Slider rasmi"),
    openapi.Parameter('title_uz',       openapi.IN_FORM, type=openapi.TYPE_STRING,  required=False, description="Sarlavha (UZ)"),
    openapi.Parameter('title_ru',       openapi.IN_FORM, type=openapi.TYPE_STRING,  required=False, description="Sarlavha (RU)"),
    openapi.Parameter('description_uz',      openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="Tavsif (UZ)"),
    openapi.Parameter('description_ru',      openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="Tavsif (RU)"),
    openapi.Parameter('sort_order', openapi.IN_FORM, type=openapi.TYPE_INTEGER, required=False, description="Tartib raqami"),
    openapi.Parameter('is_active',  openapi.IN_FORM, type=openapi.TYPE_BOOLEAN, required=False, description="Faol holati"),
]


class SliderListCreateAPIView(APIView):
    """
    GET  — barcha slayderlar ro'yxati (hamma uchun ochiq)
    POST — yangi slayder yaratish (faqat admin, multipart/form-data)
    """
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_permissions(self):
        if self.request.method == 'GET':
            return [AllowAny()]
        return [IsAdminUser()]

    @swagger_auto_schema(
        operation_summary="Slayderlar ro'yxati",
        manual_parameters=[LANG_PARAM],
        responses={200: SliderSerializer(many=True)},
        tags=["Slider"],
    )
    def get(self, request):
        lang = request.query_params.get('lang')
        qs = Slider.objects.filter(is_active=True)
        data = SliderSerializer(qs, many=True, context={'request': request}).data
        if lang:
            data = [apply_lang_filter(dict(item), lang) for item in data]
        return Response(data)

    @swagger_auto_schema(
        operation_summary="Yangi slayder yaratish",
        manual_parameters=SLIDER_WRITE_PARAMS,
        consumes=['multipart/form-data'],
        responses={201: SliderSerializer, 400: "Validatsiya xatosi", 403: "Ruxsat yo'q"},
        tags=["Slider"],
    )
    def post(self, request):
        serializer = SliderWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        return Response(
            SliderSerializer(instance, context={'request': request}).data,
            status=status.HTTP_201_CREATED,
        )


class SliderDetailAPIView(APIView):
    """
    GET    — bitta slayder
    PUT    — to'liq yangilash (faqat admin)
    PATCH  — qisman yangilash (faqat admin)
    DELETE — o'chirish (faqat admin)
    """
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_permissions(self):
        if self.request.method == 'GET':
            return [AllowAny()]
        return [IsAdminUser()]

    def _get_object(self, pk):
        try:
            return Slider.objects.get(pk=pk)
        except Slider.DoesNotExist:
            return None

    @swagger_auto_schema(
        operation_summary="Bitta slayder",
        manual_parameters=[LANG_PARAM],
        responses={200: SliderSerializer, 404: "Topilmadi"},
        tags=["Slider"],
    )
    def get(self, request, pk):
        obj = self._get_object(pk)
        if not obj:
            return Response({'detail': "Topilmadi."}, status=status.HTTP_404_NOT_FOUND)
        lang = request.query_params.get('lang')
        data = SliderSerializer(obj, context={'request': request}).data
        return Response(apply_lang_filter(dict(data), lang) if lang else data)

    @swagger_auto_schema(
        operation_summary="Slayderni to'liq yangilash",
        manual_parameters=SLIDER_WRITE_PARAMS,
        consumes=['multipart/form-data'],
        responses={200: SliderSerializer, 400: "Validatsiya xatosi", 403: "Ruxsat yo'q", 404: "Topilmadi"},
        tags=["Slider"],
    )
    def put(self, request, pk):
        obj = self._get_object(pk)
        if not obj:
            return Response({'detail': "Topilmadi."}, status=status.HTTP_404_NOT_FOUND)
        serializer = SliderWriteSerializer(obj, data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        return Response(SliderSerializer(instance, context={'request': request}).data)

    @swagger_auto_schema(
        operation_summary="Slayderni qisman yangilash",
        manual_parameters=SLIDER_WRITE_PARAMS,
        consumes=['multipart/form-data'],
        responses={200: SliderSerializer, 400: "Validatsiya xatosi", 403: "Ruxsat yo'q", 404: "Topilmadi"},
        tags=["Slider"],
    )
    def patch(self, request, pk):
        obj = self._get_object(pk)
        if not obj:
            return Response({'detail': "Topilmadi."}, status=status.HTTP_404_NOT_FOUND)
        serializer = SliderWriteSerializer(obj, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        return Response(SliderSerializer(instance, context={'request': request}).data)

    @swagger_auto_schema(
        operation_summary="Slayderni o'chirish",
        responses={204: "O'chirildi", 403: "Ruxsat yo'q", 404: "Topilmadi"},
        tags=["Slider"],
    )
    def delete(self, request, pk):
        obj = self._get_object(pk)
        if not obj:
            return Response({'detail': "Topilmadi."}, status=status.HTTP_404_NOT_FOUND)
        obj.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
