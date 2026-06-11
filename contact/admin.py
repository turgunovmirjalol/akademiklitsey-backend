from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from django.urls import reverse
from django.http import HttpResponseRedirect
from django import forms

from .models import ContactMessage


class ReplyInlineForm(forms.ModelForm):
    reply = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 4, 'style': 'width:100%'}),
        required=False,
        label="Javob yozing"
    )
    
    class Meta:
        model = ContactMessage
        fields = ['reply']


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'full_name_badge', 'email', 'phone', 
        'subject_badge', 'status_badge', 'created_at_display'
    ]
    list_filter = ['status', 'subject', 'created_at']
    search_fields = ['full_name', 'email', 'phone', 'message']
    readonly_fields = [
        'full_name', 'email', 'phone', 'subject', 'message',
        'ip_address', 'user_agent', 'created_at', 'updated_at',
        'read_at', 'replied_at', 'replied_by', 'response_time_display',
        'message_display'
    ]
    ordering = ['-created_at']
    date_hierarchy = 'created_at'
    list_per_page = 25
    
    fieldsets = (
        ("Yuboruvchi ma'lumotlari", {
            'fields': ('full_name', 'email', 'phone'),
        }),
        ("Xabar", {
            'fields': ('subject', 'message_display'),
        }),
        ("Holat", {
            'fields': ('status',),
        }),
        ("Javob", {
            'fields': ('reply', 'replied_by', 'replied_at', 'response_time_display'),
            'description': "Javob yozib, 'Saqlash' tugmasini bosing. Status avtomatik 'Javob berilgan' ga o'zgaradi.",
        }),
        ("Texnik ma'lumotlar", {
            'fields': ('ip_address', 'user_agent', 'created_at', 'updated_at', 'read_at'),
            'classes': ('collapse',),
        }),
    )
    
    def get_readonly_fields(self, request, obj=None):
        """Yangi xabar yaratishda barcha maydonlar tahrirlash mumkin"""
        if obj is None:
            return ['ip_address', 'user_agent', 'created_at', 'updated_at', 
                    'read_at', 'replied_at', 'replied_by', 'response_time_display', 'message_display']
        return self.readonly_fields
    
    def save_model(self, request, obj, form, change):
        """Javob berilganda avtomatik status va vaqtni yangilash"""
        if change and 'reply' in form.changed_data and obj.reply:
            obj.replied_by = request.user
            obj.replied_at = timezone.now()
            obj.status = ContactMessage.Status.REPLIED
        super().save_model(request, obj, form, change)
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('replied_by')
    
    # ─── Custom display metodlari ─────────────────────────────────────────────
    
    def full_name_badge(self, obj):
        color = '#dc3545' if obj.is_new else '#6c757d'
        icon = '🔴' if obj.is_new else ''
        return format_html(
            '{} <strong style="color:{}">{}</strong>',
            icon, color, obj.full_name
        )
    full_name_badge.short_description = "Ism-familiya"
    full_name_badge.admin_order_field = 'full_name'
    
    def subject_badge(self, obj):
        colors = {
            'admission': '#007bff',
            'general': '#28a745',
            'complaint': '#dc3545',
            'suggestion': '#fd7e14',
            'other': '#6c757d',
        }
        color = colors.get(obj.subject, '#6c757d')
        return format_html(
            '<span style="background:{};color:#fff;padding:2px 8px;'
            'border-radius:4px;font-size:11px">{}</span>',
            color, obj.get_subject_display()
        )
    subject_badge.short_description = "Mavzu"
    subject_badge.admin_order_field = 'subject'
    
    def status_badge(self, obj):
        configs = {
            'new': ('#dc3545', '🔴 Yangi'),
            'read': ('#fd7e14', '🟡 O\'qilgan'),
            'replied': ('#28a745', '🟢 Javob berilgan'),
            'archived': ('#6c757d', '⚫ Arxivlangan'),
        }
        color, label = configs.get(obj.status, ('#6c757d', obj.get_status_display()))
        return format_html(
            '<span style="color:{};font-weight:bold;font-size:12px">{}</span>',
            color, label
        )
    status_badge.short_description = "Holat"
    status_badge.admin_order_field = 'status'
    
    def created_at_display(self, obj):
        return obj.created_at.strftime('%d.%m.%Y %H:%M')
    created_at_display.short_description = "Yuborilgan vaqt"
    created_at_display.admin_order_field = 'created_at'
    
    def message_display(self, obj):
        """Xabarni chiroyli ko'rsatish"""
        return format_html(
            '<div style="background:#f8f9fa;padding:12px;border-left:4px solid #007bff;'
            'border-radius:4px;max-width:600px;white-space:pre-wrap">{}</div>',
            obj.message
        )
    message_display.short_description = "Xabar matni"
    
    def response_time_display(self, obj):
        """Javob berish vaqtini ko'rsatish"""
        rt = obj.response_time
        if rt is None:
            return "—"
        if rt < 1:
            return format_html('<span style="color:#28a745">{} daqiqa</span>', int(rt * 60))
        elif rt < 24:
            return format_html('<span style="color:#fd7e14">{} soat</span>', rt)
        else:
            return format_html('<span style="color:#dc3545">{} kun</span>', round(rt / 24, 1))
    response_time_display.short_description = "Javob vaqti"
    
    # ─── Admin actions ────────────────────────────────────────────────────────
    
    actions = ['mark_as_read', 'mark_as_archived', 'mark_as_new']
    
    @admin.action(description="✅ O'qilgan deb belgilash")
    def mark_as_read(self, request, queryset):
        updated = queryset.filter(status=ContactMessage.Status.NEW).update(
            status=ContactMessage.Status.READ,
            read_at=timezone.now()
        )
        self.message_user(request, f"{updated} ta xabar o'qilgan deb belgilandi.")
    
    @admin.action(description="📦 Arxivlash")
    def mark_as_archived(self, request, queryset):
        updated = queryset.update(status=ContactMessage.Status.ARCHIVED)
        self.message_user(request, f"{updated} ta xabar arxivlandi.")
    
    @admin.action(description="🔴 Yangi deb belgilash")
    def mark_as_new(self, request, queryset):
        updated = queryset.update(status=ContactMessage.Status.NEW, read_at=None)
        self.message_user(request, f"{updated} ta xabar yangi deb belgilandi.")
