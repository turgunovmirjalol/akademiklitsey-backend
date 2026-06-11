from rest_framework import serializers
from .models import ContactMessage


class ContactMessageCreateSerializer(serializers.Serializer):
    """Xabar yuborish uchun serializer (foydalanuvchilar uchun)"""
    
    full_name = serializers.CharField(
        max_length=200,
        required=True,
        help_text="To'liq ism-familiya"
    )
    email = serializers.EmailField(
        required=True,
        help_text="Email manzil"
    )
    phone = serializers.CharField(
        max_length=20,
        required=True,
        help_text="Telefon raqam (+998 90 123 45 67)"
    )
    subject = serializers.ChoiceField(
        choices=ContactMessage.Subject.choices,
        default=ContactMessage.Subject.GENERAL,
        help_text="Xabar mavzusi"
    )
    message = serializers.CharField(
        style={'base_template': 'textarea.html'},
        help_text="Xabar matni"
    )
    
    def validate_phone(self, value):
        """Telefon raqamni tekshirish"""
        import re
        # Faqat raqamlar va + belgisini qoldirish
        cleaned = re.sub(r'[^\d+]', '', value)
        if len(cleaned) < 9:
            raise serializers.ValidationError("Telefon raqam juda qisqa")
        return value
    
    def validate_message(self, value):
        """Xabar uzunligini tekshirish"""
        if len(value.strip()) < 10:
            raise serializers.ValidationError("Xabar kamida 10 ta belgidan iborat bo'lishi kerak")
        return value.strip()
    
    def create(self, validated_data):
        # IP va user agent ni request dan olish
        request = self.context.get('request')
        if request:
            validated_data['ip_address'] = self.get_client_ip(request)
            validated_data['user_agent'] = request.META.get('HTTP_USER_AGENT', '')[:500]
        
        return ContactMessage.objects.create(**validated_data)
    
    @staticmethod
    def get_client_ip(request):
        """Foydalanuvchi IP manzilini olish"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class ContactMessageListSerializer(serializers.ModelSerializer):
    """Admin uchun xabarlar ro'yxati"""
    
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
    """Admin uchun xabar detali"""
    
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
    """Xabarga javob berish uchun"""
    
    reply = serializers.CharField(
        required=True,
        style={'base_template': 'textarea.html'},
        help_text="Javob matni"
    )
    
    def validate_reply(self, value):
        if len(value.strip()) < 10:
            raise serializers.ValidationError("Javob kamida 10 ta belgidan iborat bo'lishi kerak")
        return value.strip()


class ContactMessageStatusSerializer(serializers.Serializer):
    """Xabar statusini o'zgartirish uchun"""
    
    status = serializers.ChoiceField(
        choices=ContactMessage.Status.choices,
        required=True,
        help_text="Yangi status"
    )
