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


# ─── Swagger parameters ─────────────────────────────────────────────────────

STATUS_PARAM = openapi.Parameter(
    'status', openapi.IN_QUERY,
    description="Filter by status: new | read | replied | archived",
    type=openapi.TYPE_STRING,
    enum=['new', 'read', 'replied', 'archived'],
    required=False,
)

SUBJECT_PARAM = openapi.Parameter(
    'subject', openapi.IN_QUERY,
    description="Filter by subject: admission | general | complaint | suggestion | other",
    type=openapi.TYPE_STRING,
    enum=['admission', 'general', 'complaint', 'suggestion', 'other'],
    required=False,
)


# ─── Pagination ──────────────────────────────────────────────────────────────

class ContactPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


# ─── Public: Send message ──────────────────────────────────────────────────

class ContactMessageCreateView(APIView):
    """Send message for website visitors"""
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_summary="Send message",
        operation_description=(
            "For website visitors. No authentication required.\n\n"
            "Fields:\n"
            "- `full_name` — Full name (required)\n"
            "- `email` — Email address (required)\n"
            "- `phone` — Phone number (required)\n"
            "- `subject` — Subject (optional, default: general)\n"
            "- `message` — Message text (required, min 10 characters)"
        ),
        request_body=ContactMessageCreateSerializer,
        responses={
            201: openapi.Response(
                description="Message sent successfully",
                examples={
                    "application/json": {
                        "detail": "Your message has been sent successfully. We will reply shortly.",
                        "id": 1
                    }
                }
            ),
            400: openapi.Response(description="Validation error"),
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
                "detail": "Your message has been sent successfully. We will reply shortly.",
                "id": msg.id
            },
            status=status.HTTP_201_CREATED
        )


# ─── Admin: Messages list ────────────────────────────────────────────────

class ContactMessageListView(generics.ListAPIView):
    """List all messages for admin"""
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
        operation_summary="Messages list (Admin)",
        operation_description=(
            "For authenticated admins only.\n\n"
            "Filters:\n"
            "- `?status=new|read|replied|archived`\n"
            "- `?subject=admission|general|complaint|suggestion|other`\n"
            "- `?search=...` — search by name, email, phone, message\n"
            "- `?ordering=-created_at` — sorting"
        ),
        manual_parameters=[STATUS_PARAM, SUBJECT_PARAM],
        responses={200: ContactMessageListSerializer(many=True)},
        tags=["Contact - Admin"],
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


# ─── Admin: Message detail ─────────────────────────────────────────────────────

class ContactMessageDetailView(APIView):
    """Message detail, reply and status change for admin"""
    permission_classes = [IsAuthenticated]

    def get_object(self, pk):
        return get_object_or_404(
            ContactMessage.objects.select_related('replied_by'),
            pk=pk
        )

    @swagger_auto_schema(
        operation_summary="Message detail (Admin)",
        operation_description="Full details of a single message. Automatically marked as 'read'.",
        responses={
            200: ContactMessageDetailSerializer,
            404: openapi.Response(description="Not found"),
        },
        tags=["Contact - Admin"],
    )
    def get(self, request, pk):
        msg = self.get_object(pk)
        msg.mark_as_read()  # Automatically mark as read
        serializer = ContactMessageDetailSerializer(msg)
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_summary="Delete message (Admin)",
        operation_description="Admin only. Permanently delete a message.",
        responses={
            200: openapi.Response(
                description="Deleted successfully",
                examples={"application/json": {"detail": "Message deleted."}}
            ),
            404: openapi.Response(description="Not found"),
        },
        tags=["Contact - Admin"],
    )
    def delete(self, request, pk):
        msg = self.get_object(pk)
        msg.delete()
        return Response({"detail": "Message deleted."}, status=status.HTTP_200_OK)


# ─── Admin: Reply to message ─────────────────────────────────────────────

class ContactMessageReplyView(APIView):
    """Admin replies to a message"""
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Reply to message (Admin)",
        operation_description=(
            "Admin writes a reply to a message. After replying, status automatically "
            "changes to 'replied'."
        ),
        request_body=ContactMessageReplySerializer,
        responses={
            200: ContactMessageDetailSerializer,
            400: openapi.Response(description="Validation error"),
            404: openapi.Response(description="Not found"),
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


# ─── Admin: Change status ──────────────────────────────────────────────

class ContactMessageStatusView(APIView):
    """Admin changes message status"""
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Change status (Admin)",
        operation_description="Update message status: new | read | replied | archived",
        request_body=ContactMessageStatusSerializer,
        responses={
            200: ContactMessageDetailSerializer,
            400: openapi.Response(description="Validation error"),
            404: openapi.Response(description="Not found"),
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


# ─── Admin: Statistics ───────────────────────────────────────────────────────

class ContactMessageStatsView(APIView):
    """Message statistics for admin"""
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Messages statistics (Admin)",
        operation_description="Total, new, read, replied and archived message counts.",
        responses={
            200: openapi.Response(
                description="Statistics",
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

        # By status
        status_counts = dict(
            qs.values_list('status').annotate(count=Count('id')).values_list('status', 'count')
        )

        # By subject
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