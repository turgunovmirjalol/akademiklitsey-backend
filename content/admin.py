from django.contrib import admin
from django.utils.html import format_html, mark_safe
from django.utils import timezone
from .models import News, Announcement


class BaseContentAdmin(admin.ModelAdmin):
    """News va Announcement uchun umumiy admin."""
    readonly_fields = ['views_count', 'created_at', 'slug']
    ordering = ['-published_at', '-created_at']

    def get_readonly_fields(self, request, obj=None):
        base = ['views_count', 'created_at']
        if obj:
            base.append('slug')
        return base

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

    def views_badge(self, obj):
        return format_html(
            '<span style="background:#007bff;color:#fff;padding:2px 8px;'
            'border-radius:4px;font-size:11px">👁 {}</span>',
            obj.views_count,
        )
    views_badge.short_description = "Ko'rishlar"

    def status_badge(self, obj):
        colors = {
            'published': '#28a745',
            'draft': '#6c757d',
            'archived': '#dc3545',
        }
        labels = {
            'published': 'Nashr',
            'draft': 'Qoralama',
            'archived': 'Arxiv',
        }
        color = colors.get(obj.status, '#6c757d')
        label = labels.get(obj.status, obj.status)
        return format_html(
            '<span style="background:{};color:#fff;padding:2px 8px;'
            'border-radius:4px;font-size:11px">{}</span>',
            color, label,
        )
    status_badge.short_description = "Holat"


@admin.register(News)
class NewsAdmin(BaseContentAdmin):
    list_display = [
        'title_badge', 'status_badge',
        'views_badge', 'published_at', 'created_by',
    ]
    list_filter = ['status', 'published_at', 'created_at']
    search_fields = ['title_uz', 'title_ru']
    readonly_fields = ['views_count', 'created_at', 'updated_at', 'slug', 'views_badge', 'status_badge']

    fieldsets = (
        ("O'zbek tili", {
            'fields': ('title_uz', 'content_uz'),
            'description': "Asosiy til — kamida shu til to'ldirilishi shart.",
        }),
        ("Rus tili", {
            'fields': ('title_ru', 'content_ru'),
            'classes': ('collapse',),
        }),
        ("Media", {
            'fields': ('image',),
        }),
        ("Nashr sozlamalari", {
            'fields': ('slug', 'status', 'published_at'),
        }),
        ("Statistika va tizim", {
            'fields': ('views_badge', 'created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        form.base_fields['title_uz'].required = True
        return form

    def title_badge(self, obj):
        title = obj.title_uz or obj.title_ru or obj.title_en or '—'
        return format_html('<strong>{}</strong>', title[:60] + ('...' if len(title) > 60 else ''))
    title_badge.short_description = "Sarlavha"

    def get_readonly_fields(self, request, obj=None):
        base = ['views_count', 'views_badge', 'status_badge', 'created_at', 'updated_at']
        if obj:
            base.append('slug')
        return base


@admin.register(Announcement)
class AnnouncementAdmin(BaseContentAdmin):
    list_display = [
        'title_badge', 'status_badge', 'is_important',
        'views_badge', 'expires_badge', 'published_at', 'created_by',
    ]
    list_filter = ['status', 'is_important', 'published_at', 'expires_at']
    search_fields = ['title_uz', 'title_ru']
    list_editable = ['is_important']
    readonly_fields = ['views_count', 'created_at', 'slug', 'views_badge', 'status_badge', 'expires_badge']

    fieldsets = (
        ("O'zbek tili", {
            'fields': ('title_uz', 'content_uz'),
            'description': "Asosiy til — kamida shu til to'ldirilishi shart.",
        }),
        ("Rus tili", {
            'fields': ('title_ru', 'content_ru'),
            'classes': ('collapse',),
        }),
        ("Media", {
            'fields': ('image',),
        }),
        ("Nashr sozlamalari", {
            'fields': ('slug', 'status', 'is_important', 'published_at', 'expires_at'),
        }),
        ("Statistika va tizim", {
            'fields': ('views_badge', 'expires_badge', 'created_by', 'created_at'),
            'classes': ('collapse',),
        }),
    )

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        form.base_fields['title_uz'].required = True
        return form

    def title_badge(self, obj):
        title = obj.title_uz or obj.title_ru or obj.title_en or '—'
        return format_html('<strong>{}</strong>', title[:60] + ('...' if len(title) > 60 else ''))
    title_badge.short_description = "Sarlavha"

    def expires_badge(self, obj):
        if not obj.expires_at:
            return mark_safe('<span style="color:#6c757d">Muddatsiz</span>')
        if obj.is_expired:
            return format_html(
                '<span style="color:#dc3545;font-weight:bold">Muddati tugagan: {}</span>',
                obj.expires_at.strftime('%d.%m.%Y'),
            )
        return format_html(
            '<span style="color:#28a745">{}</span>',
            obj.expires_at.strftime('%d.%m.%Y %H:%M'),
        )
    expires_badge.short_description = "Muddat"

    def get_readonly_fields(self, request, obj=None):
        base = ['views_count', 'views_badge', 'status_badge', 'expires_badge', 'created_at']
        if obj:
            base.append('slug')
        return base
