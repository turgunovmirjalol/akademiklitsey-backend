from rest_framework import serializers
from .models import ContactMessage


class ContactMessageCreateSerializer(serializers.Serializer):
    """Serializer for sending messages (for users)"""

    full_name = serializers.CharField(
        max_length=200,
        required=True,
        help_text="Full name"
    )
    email = serializers.EmailField(
        required=True,
        help_text="Email address"
    )
    phone = serializers.CharField(
        max_length=20,
        required=True,
        help_text="Phone number (+998 90 123 45 67)"
    )
    subject = serializers.ChoiceField(
        choices=ContactMessage.Subject.choices,
        default=ContactMessage.Subject.GENERAL,
        help_text="Message subject"
    )
    message = serializers.CharField(
        style={'base_template': 'textarea.html'},
        help_text="Message text"
    )

    def validate_phone(self, value):
        """Validate phone number"""
        import re
        # Keep only digits and + sign
        cleaned = re.sub(r'[^\d+]', '', value)
        if len(cleaned) < 9:
            raise serializers.ValidationError("Phone number is too short")
        return value

    def validate_message(self, value):
        """Validate message length"""
        if len(value.strip()) < 10:
            raise serializers.ValidationError("Message must be at least 10 characters long")
        return value.strip()

    def create(self, validated_data):
        # Get IP and user agent from request
        request = self.context.get('request')
        if request:
            validated_data['ip_address'] = self.get_client_ip(request)
            validated_data['user_agent'] = request.META.get('HTTP_USER_AGENT', '')[:500]

        return ContactMessage.objects.create(**validated_data)

    @staticmethod
    def get_client_ip(request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class ContactMessageListSerializer(serializers.ModelSerializer):
    """Messages list serializer for admin"""

    status_display = serializers.CharField(source='get_status_display', read_only=True)
    subject_display = serializers.CharField(source='get_subject_display', read_only=True)
    is_new = serializers.BooleanField(read_only=True)
    response_time = serializers.FloatField(read_only=True)

    class Meta:
        model = ContactMessage
        fields = [
            'id', 'full_name', 'email', 'phone', 'subject', 'subject_display',
            'message', 'status', 'status_display', 'is_new', 'response_time',
            'created_at', 'read_at', 'replied_at'
        ]
        read_only_fields = fields


class ContactMessageDetailSerializer(serializers.ModelSerializer):
    """Message detail serializer for admin"""

    status_display = serializers.CharField(source='get_status_display', read_only=True)
    subject_display = serializers.CharField(source='get_subject_display', read_only=True)
    replied_by_name = serializers.SerializerMethodField()
    is_new = serializers.BooleanField(read_only=True)
    response_time = serializers.FloatField(read_only=True)

    class Meta:
        model = ContactMessage
        fields = [
            'id', 'full_name', 'email', 'phone', 'subject', 'subject_display',
            'message', 'status', 'status_display', 'reply', 'replied_by',
            'replied_by_name', 'replied_at', 'is_new', 'response_time',
            'ip_address', 'user_agent', 'created_at', 'updated_at', 'read_at'
        ]
        read_only_fields = [
            'id', 'created_at', 'updated_at', 'read_at', 'replied_at',
            'replied_by', 'ip_address', 'user_agent'
        ]

    def get_replied_by_name(self, obj):
        if obj.replied_by:
            return f"{obj.replied_by.first_name} {obj.replied_by.last_name}".strip() or obj.replied_by.username
        return None


class ContactMessageReplySerializer(serializers.Serializer):
    """Serializer for replying to messages"""

    reply = serializers.CharField(
        required=True,
        style={'base_template': 'textarea.html'},
        help_text="Reply text"
    )

    def validate_reply(self, value):
        if len(value.strip()) < 10:
            raise serializers.ValidationError("Reply must be at least 10 characters long")
        return value.strip()


class ContactMessageStatusSerializer(serializers.Serializer):
    """Serializer for changing message status"""

    status = serializers.ChoiceField(
        choices=ContactMessage.Status.choices,
        required=True,
        help_text="New status"
    )