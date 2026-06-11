from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from .models import User


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Token javobida user rolini qo'shadigan maxsus serializer"""
    def validate(self, attrs):
        data = super().validate(attrs)

        data['role'] = self.user.role

        return data


class UserSerializer(serializers.ModelSerializer):
    """Umumiy foydalanish uchun user serializeri"""
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'role',
                  'is_staff', 'is_superuser', 'is_active', 'date_joined')
        read_only_fields = ('id', 'date_joined')


class ChangePasswordSerializer(serializers.Serializer):
    """Parolni o'zgartirish uchun serializer"""
    old_password = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'},
        help_text="Joriy parolingizni kiriting"
    )
    new_password = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'},
        help_text="Yangi parolingizni kiriting"
    )
    confirm_password = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'},
        help_text="Yangi parolingizni takrorlang"
    )

    def validate_old_password(self, value):
        """Eski parolni tekshirish"""
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Joriy parol noto'g'ri kiritilgan.")
        return value

    def validate_new_password(self, value):
        """Yangi parolni Django validatorlari bilan tekshirish"""
        user = self.context['request'].user
        try:
            validate_password(value, user)
        except ValidationError as e:
            raise serializers.ValidationError(list(e.messages))
        return value

    def validate(self, attrs):
        """Yangi parol va tasdiqlash parolini solishtirish"""
        if attrs['new_password'] != attrs['confirm_password']:
            raise serializers.ValidationError({
                'confirm_password': "Yangi parol va tasdiqlash paroli bir xil bo'lishi kerak."
            })
        
        # Yangi parol eski parol bilan bir xil bo'lmasligi kerak
        if attrs['old_password'] == attrs['new_password']:
            raise serializers.ValidationError({
                'new_password': "Yangi parol eski paroldan farqli bo'lishi kerak."
            })
        
        return attrs

    def save(self, **kwargs):
        """Yangi parolni saqlash"""
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user
