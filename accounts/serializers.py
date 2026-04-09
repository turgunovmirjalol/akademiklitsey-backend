from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework import serializers
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
