from rest_framework import generics, filters, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from accounts.permissions import IsAdminUser, IsAdminOrReadOnly
from .models import Statistic
from .serializers import (
    StatisticSerializer,
    StatisticWriteSerializer,
    StatisticBulkUpdateSerializer,
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


# ─────────────────────────────────────────────────────────────────────────────
# Statistic
# ─────────────────────────────────────────────────────────────────────────────

class StatisticListCreateView(APIView):
    """
    GET  — barcha statistikalar (hamma ko'rishi mumkin)
    POST — yangi statistika yaratish (faqat admin)
    """
    parser_classes = []  # JSON only — rasm/fayl yo'q

    def get_permissions(self):
        if self.request.method == 'GET':
            return [AllowAny()]
        return [IsAdminUser()]

    @swagger_auto_schema(
        operation_summary="Statistikalar ro'yxati",
        operation_description=(
            "Bosh sahifa uchun barcha statistikalar.\n\n"
            "- `?lang=uz|ru|en|uz_cyrl` — faqat o'sha tildagi label"
        ),
        manual_parameters=[LANG_PARAM],
        responses={200: StatisticSerializer(many=True)},
        tags=["Main - Statistics"],
    )
    def get(self, request):
        lang = request.query_params.get('lang')
        qs = Statistic.objects.all().order_by('sort_order')
        data = StatisticSerializer(qs, many=True).data
        return Response(apply_lang_filter(list(data), lang))

    @swagger_auto_schema(
        operation_summary="Yangi statistika yaratish",
        operation_description=(
            "Faqat admin.\n\n"
            "Har bir til uchun label alohida maydon.\n"
            "Kamida bitta tilda `label_*` to'ldirilishi shart.\n\n"
            "`key` — unikal texnik identifikator (masalan: `students_count`)"
        ),
        request_body=StatisticWriteSerializer,
        responses={
            201: StatisticSerializer,
            400: openapi.Response(description="Validatsiya xatosi"),
            403: openapi.Response(description="Ruxsat yo'q"),
        },
        tags=["Main - Statistics"],
    )
    def post(self, request):
        serializer = StatisticWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        stat = serializer.save()
        return Response(StatisticSerializer(stat).data, status=status.HTTP_201_CREATED)


class StatisticDetailView(APIView):
    """
    GET    — bitta statistika (hamma ko'rishi mumkin)
    PUT    — to'liq yangilash (faqat admin)
    PATCH  — qisman yangilash (faqat admin)
    DELETE — o'chirish (faqat admin)
    """
    parser_classes = []

    def get_permissions(self):
        if self.request.method == 'GET':
            return [AllowAny()]
        return [IsAdminUser()]

    def _get_object(self, pk):
        return get_object_or_404(Statistic, pk=pk)

    @swagger_auto_schema(
        operation_summary="Statistika detali",
        manual_parameters=[LANG_PARAM],
        responses={200: StatisticSerializer, 404: openapi.Response(description="Topilmadi")},
        tags=["Main - Statistics"],
    )
    def get(self, request, pk):
        lang = request.query_params.get('lang')
        stat = self._get_object(pk)
        data = StatisticSerializer(stat).data
        return Response(apply_lang_filter(data, lang))

    @swagger_auto_schema(
        operation_summary="Statistikani to'liq yangilash",
        request_body=StatisticWriteSerializer,
        responses={200: StatisticSerializer, 400: openapi.Response(description="Validatsiya xatosi")},
        tags=["Main - Statistics"],
    )
    def put(self, request, pk):
        stat = self._get_object(pk)
        serializer = StatisticWriteSerializer(stat, data=request.data)
        serializer.is_valid(raise_exception=True)
        stat = serializer.save()
        return Response(StatisticSerializer(stat).data)

    @swagger_auto_schema(
        operation_summary="Statistikani qisman yangilash",
        operation_description="Faqat o'zgartirilishi kerak bo'lgan maydonlar yuboriladi.",
        request_body=StatisticWriteSerializer,
        responses={200: StatisticSerializer, 400: openapi.Response(description="Validatsiya xatosi")},
        tags=["Main - Statistics"],
    )
    def patch(self, request, pk):
        stat = self._get_object(pk)
        serializer = StatisticWriteSerializer(stat, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        stat = serializer.save()
        return Response(StatisticSerializer(stat).data)

    @swagger_auto_schema(
        operation_summary="Statistikani o'chirish",
        responses={200: openapi.Response(description="Muvaffaqiyatli o'chirildi")},
        tags=["Main - Statistics"],
    )
    def delete(self, request, pk):
        stat = self._get_object(pk)
        data = {
            'id': stat.pk,
            'key': stat.key,
            'detail': "Statistika muvaffaqiyatli o'chirildi.",
        }
        stat.delete()
        return Response(data, status=status.HTTP_200_OK)


class StatisticBulkUpdateView(APIView):
    """
    POST /statistics/bulk-update/ — bir nechta statistikani bir vaqtda yangilash.
    Faqat value yangilanadi (key orqali topiladi).
    """
    permission_classes = [IsAdminUser]

    @swagger_auto_schema(
        operation_summary="Bir nechta statistikani bir vaqtda yangilash",
        operation_description=(
            "Faqat admin. Faqat `value` yangilanadi.\n\n"
            "Misol:\n"
            "```json\n"
            '{"updates": [{"key": "students_count", "value": 1200}, {"key": "teachers_count", "value": 85}]}\n'
            "```"
        ),
        request_body=StatisticBulkUpdateSerializer,
        responses={
            200: openapi.Response(
                description="Yangilangan statistikalar",
                examples={
                    "application/json": {
                        "updated": 2,
                        "not_found": [],
                        "statistics": []
                    }
                }
            ),
            400: openapi.Response(description="Validatsiya xatosi"),
        },
        tags=["Main - Statistics"],
    )
    def post(self, request):
        serializer = StatisticBulkUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        updates = serializer.validated_data['updates']
        updated = []
        not_found = []

        for item in updates:
            key = item['key']
            value = int(item['value'])
            count = Statistic.objects.filter(key=key).update(value=value)
            if count:
                updated.append(key)
            else:
                not_found.append(key)

        stats = Statistic.objects.filter(key__in=updated).order_by('sort_order')
        return Response({
            'updated': len(updated),
            'not_found': not_found,
            'statistics': StatisticSerializer(stats, many=True).data,
        })
