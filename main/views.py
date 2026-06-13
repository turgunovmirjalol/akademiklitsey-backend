from rest_framework import generics, filters, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView
from rest_framework.parsers import JSONParser
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

# ─── Swagger parameters ─────────────────────────────────────────────────────

LANG_PARAM = openapi.Parameter(
    'lang', openapi.IN_QUERY,
    description="Filter response language: uz | ru",
    type=openapi.TYPE_STRING,
    enum=['uz', 'ru'],
    required=False,
)


# ─────────────────────────────────────────────────────────────────────────────
# Statistic
# ─────────────────────────────────────────────────────────────────────────────

class StatisticListCreateView(APIView):
    """
    GET  — all statistics (everyone can view)
    POST — create new statistic (admin only)
    """
    parser_classes = [JSONParser]

    def get_permissions(self):
        if self.request.method == 'GET':
            return [AllowAny()]
        return [IsAdminUser()]

    @swagger_auto_schema(
        operation_summary="Statistics list",
        operation_description=(
            "All statistics for the homepage.\n\n"
            "- `?lang=uz|ru` — show only that language label"
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
        operation_summary="Create new statistic",
        operation_description=(
            "Admin only.\n\n"
            "Label for each language is a separate field.\n"
            "At least one language `label_*` must be filled.\n\n"
            "`key` — unique technical identifier (e.g.: `students_count`)"
        ),
        request_body=StatisticWriteSerializer,
        responses={
            201: StatisticSerializer,
            400: openapi.Response(description="Validation error"),
            403: openapi.Response(description="Permission denied"),
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
    GET    — single statistic (everyone can view)
    PUT    — full update (admin only)
    PATCH  — partial update (admin only)
    DELETE — delete (admin only)
    """
    parser_classes = [JSONParser]

    def get_permissions(self):
        if self.request.method == 'GET':
            return [AllowAny()]
        return [IsAdminUser()]

    def _get_object(self, pk):
        return get_object_or_404(Statistic, pk=pk)

    @swagger_auto_schema(
        operation_summary="Statistic detail",
        manual_parameters=[LANG_PARAM],
        responses={200: StatisticSerializer, 404: openapi.Response(description="Not found")},
        tags=["Main - Statistics"],
    )
    def get(self, request, pk):
        lang = request.query_params.get('lang')
        stat = self._get_object(pk)
        data = StatisticSerializer(stat).data
        return Response(apply_lang_filter(data, lang))

    @swagger_auto_schema(
        operation_summary="Update statistic completely",
        request_body=StatisticWriteSerializer,
        responses={200: StatisticSerializer, 400: openapi.Response(description="Validation error")},
        tags=["Main - Statistics"],
    )
    def put(self, request, pk):
        stat = self._get_object(pk)
        serializer = StatisticWriteSerializer(stat, data=request.data)
        serializer.is_valid(raise_exception=True)
        stat = serializer.save()
        return Response(StatisticSerializer(stat).data)

    @swagger_auto_schema(
        operation_summary="Update statistic partially",
        operation_description="Only fields that need to be changed are sent.",
        request_body=StatisticWriteSerializer,
        responses={200: StatisticSerializer, 400: openapi.Response(description="Validation error")},
        tags=["Main - Statistics"],
    )
    def patch(self, request, pk):
        stat = self._get_object(pk)
        serializer = StatisticWriteSerializer(stat, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        stat = serializer.save()
        return Response(StatisticSerializer(stat).data)

    @swagger_auto_schema(
        operation_summary="Delete statistic",
        responses={200: openapi.Response(description="Deleted successfully")},
        tags=["Main - Statistics"],
    )
    def delete(self, request, pk):
        stat = self._get_object(pk)
        data = {
            'id': stat.pk,
            'key': stat.key,
            'detail': "Statistic deleted successfully.",
        }
        stat.delete()
        return Response(data, status=status.HTTP_200_OK)


class StatisticBulkUpdateView(APIView):
    """
    POST /statistics/bulk-update/ — update multiple statistics at once.
    Only value is updated (found by key).
    """
    permission_classes = [IsAdminUser]

    @swagger_auto_schema(
        operation_summary="Update multiple statistics at once",
        operation_description=(
            "Admin only. Only `value` is updated.\n\n"
            "Example:\n"
            "```json\n"
            '{"updates": [{"key": "students_count", "value": 1200}, {"key": "teachers_count", "value": 85}]}\n'
            "```"
        ),
        request_body=StatisticBulkUpdateSerializer,
        responses={
            200: openapi.Response(
                description="Updated statistics",
                examples={
                    "application/json": {
                        "updated": 2,
                        "not_found": [],
                        "statistics": []
                    }
                }
            ),
            400: openapi.Response(description="Validation error"),
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