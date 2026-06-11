from rest_framework import generics, filters, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView
from rest_framework.pagination import PageNumberPagination
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from accounts.permissions import IsAdminOrReadOnly
from .models import ContactMessage
from .serializers import (
    ContactMessageCreateSerializer,
    ContactMessageListSerializer,
    ContactMessageDetailSerializer,
    ContactMessageReplySerializer,
    ContactMessageStatusSerializer,
)


# ─── Swagger parametrlar ─────────────────────────────────────────────────────

STATUS_PARAM = openapi.Parameter(
    'status', openapi.IN_QUERY,
    description="Holat bo'yicha filter: new | read | replied | archived",
    type=openapi.TYPE_STRING,
    enum=['new', 'read', 'replied', 'archived'],
    required=False,
)

SUBJECT_PARAM = openapi.Parameter(
    'subject', openapi.IN_QUERY,
    description="Mavzu bo'yicha filter: admission | general | complaint | suggestion | other",
    type=openapi.TYPE_STRING,
    enum=['admission', 'general', 'complaint', 'suggestion', 'other'],
    required=False,
)


# ─── Pagination ──────────────────────────────────────────────────────────────

class ContactPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


# ─── Public: Xabar yuborish ──────────────────────────────────────────────────

class ContactMessageCreateView(APIView):
    """Sayt tashrif buyuruvchilari uchun xabar yuborish"""
    permission_classes = [AllowAny]
    
    @swagger_auto_schema(
        operation_summary="Xabar yuborish",
        operation_description=(
            "Sayt tashrif buyuruvchilari uchun. Hech qanday autentifikatsiya talab qilinmaydi.\n\n"
            "Maydonlar:\n"
            "- `full_name` — Ism-familiya (majburiy)\n"
            "- `email` — Email manzil (majburiy)\n"
            "- `phone` — Telefon raqam (majburiy)\n"
            "- `subject` — Mavzu (ixtiyoriy, default: general)\n"
            "- `message` — Xabar matni (majburiy, min 10 belgi)"
        ),
        request_body=ContactMessageCreateSerializer,
        responses={
            201: openapi.Response(
                description="Xabar muvaffaqiyatli yuborildi",
                examples={
                    "application/json": {
                        "detail": "Xabaringiz muvaffaqiyatli yuborildi. Tez orada javob beramiz.",
                        "id": 1
                    }
                }
            ),
            400: openapi.Response(description="Validatsiya xatosi"),
        },
        tags=["Contact - Public"],
    )
    def post(self, request):
        serializer = ContactMessageCreateSerializer(
            data=request.data, 
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        msg = serializer.save()
        return Response(
            {
                "detail": "Xabaringiz muvaffaqiyatli yuborildi. Tez orada javob beramiz.",
                "id": msg.id
            },
            status=status.HTTP_201_CREATED
        )


# ─── Admin: Xabarlar ro'yxati ────────────────────────────────────────────────

class ContactMessageListView(generics.ListAPIView):
    """Admin uchun barcha xabarlar ro'yxati"""
    permission_classes = [IsAuthenticated]
    serializer_class = ContactMessageListSerializer
    pagination_class = ContactPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'subject']
    search_fields = ['full_name', 'email', 'phone', 'message', 'subject']
    ordering_fields = ['created_at', 'status', 'subject']
    ordering = ['-created_at']
    
    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return ContactMessage.objects.none()
        return ContactMessage.objects.select_related('replied_by').all()
    
    @swagger_auto_schema(
        operation_summary="Xabarlar ro'yxati (Admin)",
        operation_description=(
            "Faqat autentifikatsiyadan o'tgan adminlar uchun.\n\n"
            "Filterlar:\n"
            "- `?status=new|read|replied|archived`\n"
            "- `?subject=admission|general|complaint|suggestion|other`\n"
            "- `?search=...` — ism, email, telefon, xabar bo'yicha qidirish\n"
            "- `?ordering=-created_at` — tartiblash"
        ),
        manual_parameters=[STATUS_PARAM, SUBJECT_PARAM],
        responses={200: ContactMessageListSerializer(many=True)},
        tags=["Contact - Admin"],
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


# ─── Admin: Xabar detali ─────────────────────────────────────────────────────

class ContactMessageDetailView(APIView):
    """Admin uchun xabar detali, javob berish va status o'zgartirish"""
    permission_classes = [IsAuthenticated]
    
    def get_object(self, pk):
        return get_object_or_404(
            ContactMessage.objects.select_related('replied_by'), 
            pk=pk
        )
    
    @swagger_auto_schema(
        operation_summary="Xabar detali (Admin)",
        operation_description="Bitta xabarning to'liq ma'lumotlari. Avtomatik 'o'qilgan' deb belgilanadi.",
        responses={
            200: ContactMessageDetailSerializer,
            404: openapi.Response(description="Topilmadi"),
        },
        tags=["Contact - Admin"],
    )
    def get(self, request, pk):
        msg = self.get_object(pk)
        msg.mark_as_read()  # Avtomatik o'qilgan deb belgilash
        serializer = ContactMessageDetailSerializer(msg)
        return Response(serializer.data)
    
    @swagger_auto_schema(
        operation_summary="Xabarni o'chirish (Admin)",
        operation_description="Faqat admin. Xabarni butunlay o'chirish.",
        responses={
            200: openapi.Response(
                description="Muvaffaqiyatli o'chirildi",
                examples={"application/json": {"detail": "Xabar o'chirildi."}}
            ),
            404: openapi.Response(description="Topilmadi"),
        },
        tags=["Contact - Admin"],
    )
    def delete(self, request, pk):
        msg = self.get_object(pk)
        msg.delete()
        return Response({"detail": "Xabar o'chirildi."}, status=status.HTTP_200_OK)


# ─── Admin: Xabarga javob berish ─────────────────────────────────────────────

class ContactMessageReplyView(APIView):
    """Admin xabarga javob beradi"""
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_summary="Xabarga javob berish (Admin)",
        operation_description=(
            "Admin xabarga javob yozadi. Javob berilgandan so'ng status avtomatik "
            "'replied' ga o'zgaradi."
        ),
        request_body=ContactMessageReplySerializer,
        responses={
            200: ContactMessageDetailSerializer,
            400: openapi.Response(description="Validatsiya xatosi"),
            404: openapi.Response(description="Topilmadi"),
        },
        tags=["Contact - Admin"],
    )
    def post(self, request, pk):
        msg = get_object_or_404(ContactMessage, pk=pk)
        serializer = ContactMessageReplySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        msg.mark_as_replied(
            reply_text=serializer.validated_data['reply'],
            user=request.user
        )
        
        return Response(
            ContactMessageDetailSerializer(msg).data,
            status=status.HTTP_200_OK
        )


# ─── Admin: Status o'zgartirish ──────────────────────────────────────────────

class ContactMessageStatusView(APIView):
    """Admin xabar statusini o'zgartiradi"""
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_summary="Status o'zgartirish (Admin)",
        operation_description="Xabar statusini yangilash: new | read | replied | archived",
        request_body=ContactMessageStatusSerializer,
        responses={
            200: ContactMessageDetailSerializer,
            400: openapi.Response(description="Validatsiya xatosi"),
            404: openapi.Response(description="Topilmadi"),
        },
        tags=["Contact - Admin"],
    )
    def patch(self, request, pk):
        msg = get_object_or_404(ContactMessage, pk=pk)
        serializer = ContactMessageStatusSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        msg.status = serializer.validated_data['status']
        msg.save(update_fields=['status', 'updated_at'])
        
        return Response(
            ContactMessageDetailSerializer(msg).data,
            status=status.HTTP_200_OK
        )


# ─── Admin: Statistika ───────────────────────────────────────────────────────

class ContactMessageStatsView(APIView):
    """Admin uchun xabarlar statistikasi"""
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_summary="Xabarlar statistikasi (Admin)",
        operation_description="Jami, yangi, o'qilgan, javob berilgan va arxivlangan xabarlar soni.",
        responses={
            200: openapi.Response(
                description="Statistika",
                examples={
                    "application/json": {
                        "total": 50,
                        "new": 10,
                        "read": 15,
                        "replied": 20,
                        "archived": 5,
                        "by_subject": {
                            "admission": 20,
                            "general": 15,
                            "complaint": 5,
                            "suggestion": 7,
                            "other": 3
                        }
                    }
                }
            )
        },
        tags=["Contact - Admin"],
    )
    def get(self, request):
        from django.db.models import Count
        
        qs = ContactMessage.objects.all()
        
        # Status bo'yicha
        status_counts = dict(
            qs.values_list('status').annotate(count=Count('id')).values_list('status', 'count')
        )
        
        # Mavzu bo'yicha
        subject_counts = dict(
            qs.values_list('subject').annotate(count=Count('id')).values_list('subject', 'count')
        )
        
        return Response({
            "total": qs.count(),
            "new": status_counts.get('new', 0),
            "read": status_counts.get('read', 0),
            "replied": status_counts.get('replied', 0),
            "archived": status_counts.get('archived', 0),
            "by_subject": {
                "admission": subject_counts.get('admission', 0),
                "general": subject_counts.get('general', 0),
                "complaint": subject_counts.get('complaint', 0),
                "suggestion": subject_counts.get('suggestion', 0),
                "other": subject_counts.get('other', 0),
            }
        })
