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

# ─── Reusable Swagger parameters ──────────────────────────────────────────

LANG_PARAM = openapi.Parameter(
    'lang', openapi.IN_QUERY,
    description="Filter response language: uz | ru",
    type=openapi.TYPE_STRING,
    enum=['uz', 'ru'],
    required=False,
)

# Multilingual fields — for POST/PUT/PATCH
MULTILANG_PARAMS = [
    openapi.Parameter('short_name_uz',      openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="Short name (Uzbek Latin)"),
    openapi.Parameter('short_name_ru',      openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="Short name (Russian)"),
    openapi.Parameter('full_name_uz',       openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="Full name (Uzbek Latin)"),
    openapi.Parameter('full_name_ru',       openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="Full name (Russian)"),
    openapi.Parameter('address_uz',         openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="Address (Uzbek Latin)"),
    openapi.Parameter('address_ru',         openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="Address (Russian)"),
]

COMMON_PARAMS = [
    openapi.Parameter('established_year', openapi.IN_FORM, type=openapi.TYPE_INTEGER, required=False, description="Established year"),
    openapi.Parameter('phone',    openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="Phone number"),
    openapi.Parameter('email',    openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="Email address"),
    openapi.Parameter('website',  openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="Website URL"),
    openapi.Parameter('logo',     openapi.IN_FORM, type=openapi.TYPE_FILE,   required=False, description="Logo image"),
    openapi.Parameter('telegram', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="Telegram URL"),
    openapi.Parameter('instagram',openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="Instagram URL"),
    openapi.Parameter('facebook', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="Facebook URL"),
    openapi.Parameter('youtube',  openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="YouTube URL"),
]

ALL_WRITE_PARAMS = MULTILANG_PARAMS + COMMON_PARAMS


class SiteSettingsAPIView(APIView):
    """
    GET   — get site settings (open to everyone)
    PUT   — full update (admin only)
    PATCH — partial update (admin only)
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
                address_uz="Tashkent city",
                established_year=2000,
            )
        return instance

    @swagger_auto_schema(
        operation_summary="Get site settings",
        operation_description=(
            "General information about the site: name, address, contact, logo, social networks.\n\n"
            "`?lang=uz|ru` — returns only that language translation."
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
        operation_summary="Update settings completely",
        operation_description="Admin only. All fields must be sent. **`multipart/form-data`**.",
        manual_parameters=ALL_WRITE_PARAMS,
        consumes=['multipart/form-data'],
        responses={
            200: SiteSettingsSerializer,
            400: openapi.Response(description="Validation error"),
            403: openapi.Response(description="Permission denied"),
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
        operation_summary="Update settings partially",
        operation_description="Admin only. Only fields that need to be changed. **`multipart/form-data`**.",
        manual_parameters=ALL_WRITE_PARAMS,
        consumes=['multipart/form-data'],
        responses={
            200: SiteSettingsSerializer,
            400: openapi.Response(description="Validation error"),
            403: openapi.Response(description="Permission denied"),
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
    openapi.Parameter('image',          openapi.IN_FORM, type=openapi.TYPE_FILE,    required=False, description="Slider image"),
    openapi.Parameter('title_uz',       openapi.IN_FORM, type=openapi.TYPE_STRING,  required=False, description="Title (UZ)"),
    openapi.Parameter('title_ru',       openapi.IN_FORM, type=openapi.TYPE_STRING,  required=False, description="Title (RU)"),
    openapi.Parameter('description_uz',      openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="Description (UZ)"),
    openapi.Parameter('description_ru',      openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="Description (RU)"),
    openapi.Parameter('sort_order', openapi.IN_FORM, type=openapi.TYPE_INTEGER, required=False, description="Sort order"),
    openapi.Parameter('is_active',  openapi.IN_FORM, type=openapi.TYPE_BOOLEAN, required=False, description="Active status"),
]


class SliderListCreateAPIView(APIView):
    """
    GET  — all sliders list (open to everyone)
    POST — create new slider (admin only, multipart/form-data)
    """
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_permissions(self):
        if self.request.method == 'GET':
            return [AllowAny()]
        return [IsAdminUser()]

    @swagger_auto_schema(
        operation_summary="Sliders list",
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
        operation_summary="Create new slider",
        manual_parameters=SLIDER_WRITE_PARAMS,
        consumes=['multipart/form-data'],
        responses={201: SliderSerializer, 400: "Validation error", 403: "Permission denied"},
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
    GET    — single slider
    PUT    — full update (admin only)
    PATCH  — partial update (admin only)
    DELETE — delete (admin only)
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
        operation_summary="Single slider",
        manual_parameters=[LANG_PARAM],
        responses={200: SliderSerializer, 404: "Not found"},
        tags=["Slider"],
    )
    def get(self, request, pk):
        obj = self._get_object(pk)
        if not obj:
            return Response({'detail': "Not found."}, status=status.HTTP_404_NOT_FOUND)
        lang = request.query_params.get('lang')
        data = SliderSerializer(obj, context={'request': request}).data
        return Response(apply_lang_filter(dict(data), lang) if lang else data)

    @swagger_auto_schema(
        operation_summary="Update slider completely",
        manual_parameters=SLIDER_WRITE_PARAMS,
        consumes=['multipart/form-data'],
        responses={200: SliderSerializer, 400: "Validation error", 403: "Permission denied", 404: "Not found"},
        tags=["Slider"],
    )
    def put(self, request, pk):
        obj = self._get_object(pk)
        if not obj:
            return Response({'detail': "Not found."}, status=status.HTTP_404_NOT_FOUND)
        serializer = SliderWriteSerializer(obj, data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        return Response(SliderSerializer(instance, context={'request': request}).data)

    @swagger_auto_schema(
        operation_summary="Update slider partially",
        manual_parameters=SLIDER_WRITE_PARAMS,
        consumes=['multipart/form-data'],
        responses={200: SliderSerializer, 400: "Validation error", 403: "Permission denied", 404: "Not found"},
        tags=["Slider"],
    )
    def patch(self, request, pk):
        obj = self._get_object(pk)
        if not obj:
            return Response({'detail': "Not found."}, status=status.HTTP_404_NOT_FOUND)
        serializer = SliderWriteSerializer(obj, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        return Response(SliderSerializer(instance, context={'request': request}).data)

    @swagger_auto_schema(
        operation_summary="Delete slider",
        responses={204: "Deleted", 403: "Permission denied", 404: "Not found"},
        tags=["Slider"],
    )
    def delete(self, request, pk):
        obj = self._get_object(pk)
        if not obj:
            return Response({'detail': "Not found."}, status=status.HTTP_404_NOT_FOUND)
        obj.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)