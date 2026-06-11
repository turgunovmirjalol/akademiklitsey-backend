from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    
    list_display = ('username', 'email', 'first_name', 'last_name', 'role', 'is_active', 'date_joined')
    list_filter = ('role', 'is_active', 'is_staff', 'is_superuser')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    ordering = ('-date_joined',)
    
    fieldsets = (
        (_('Asosiy ma\'lumotlar'), {
            'fields': ('username', 'email', 'password')
        }),
        (_('Shaxsiy ma\'lumotlar'), {
            'fields': ('first_name', 'last_name')
        }),
        (_('Ruxsatlar'), {
            'fields': ('role', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')
        }),
        (_('Muhim sanalar'), {
            'fields': ('last_login', 'date_joined'),
            'classes': ('collapse',)
        }),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2', 'role'),
        }),
    )
    
    readonly_fields = ('last_login', 'date_joined')
    
    def get_queryset(self, request):
        """Adminlar faqat userlarni ko'ra oladi"""
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        # Oddiy adminlar faqat userlarni ko'radi, adminlarni emas
        return qs.filter(role=User.ROLE_USER)
    
    def get_form(self, request, obj=None, **kwargs):
        """Form fieldlarini sozlash"""
        form = super().get_form(request, obj, **kwargs)
        
        # Superuser bo'lmasa, some fieldlarni disable qilish
        if not request.user.is_superuser:
            if 'is_superuser' in form.base_fields:
                form.base_fields['is_superuser'].disabled = True
            if 'groups' in form.base_fields:
                form.base_fields['groups'].disabled = True
            if 'user_permissions' in form.base_fields:
                form.base_fields['user_permissions'].disabled = True
        
        # O'zini o'zini tahrirlashda role ni o'zgartirib bo'lmaydi
        if obj and obj == request.user and not request.user.is_superuser:
            if 'role' in form.base_fields:
                form.base_fields['role'].disabled = True
        
        return form
