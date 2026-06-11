from django.contrib import admin
from django.utils.html import format_html, mark_safe
from .models import SiteSettings, Slider


@admin.register(Slider)
class SliderAdmin(admin.ModelAdmin):
    list_display = ['image_preview', '__str__', 'sort_order', 'is_active']
    list_editable = ['sort_order', 'is_active']
    list_display_links = ['image_preview', '__str__']

    fieldsets = (
        ("Rasm", {'fields': ('image', 'image_preview')}),
        ("O'zbek tili (Lotin)",  {'fields': ('title_uz', 'description_uz')}),
        ("O'zbek tili (Kirill)", {'fields': ('title_uz_cyrl', 'description_uz_cyrl'), 'classes': ('collapse',)}),
        ("Rus tili",             {'fields': ('title_ru', 'description_ru'), 'classes': ('collapse',)}),
        ("Ingliz tili",          {'fields': ('title_en', 'description_en'), 'classes': ('collapse',)}),
        ("Sozlamalar",           {'fields': ('sort_order', 'is_active')}),
    )
    readonly_fields = ['image_preview']

    def image_preview(self, obj):
        if obj and obj.image:
            return format_html(
                '<img src="{}" style="height:80px;border-radius:6px;border:1px solid #ddd;" />',
                obj.image.url,
            )
        return mark_safe('<span style="color:#999">Rasm yuklanmagan</span>')
    image_preview.short_description = "Ko'rinish"


@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    list_display = ['logo_preview', '__str__', 'phone', 'email', 'established_year']

    fieldsets = (
        ("O'zbek tili (Lotin)", {
            'fields': ('short_name_uz', 'full_name_uz', 'address_uz'),
            'description': "Asosiy til — kamida shu til to'ldirilishi shart.",
        }),
        ("O'zbek tili (Kirill)", {
            'fields': ('short_name_uz_cyrl', 'full_name_uz_cyrl', 'address_uz_cyrl'),
            'classes': ('collapse',),
        }),
        ("Rus tili", {
            'fields': ('short_name_ru', 'full_name_ru', 'address_ru'),
            'classes': ('collapse',),
        }),
        ("Ingliz tili", {
            'fields': ('short_name_en', 'full_name_en', 'address_en'),
            'classes': ('collapse',),
        }),
        ("Aloqa ma'lumotlari", {
            'fields': ('phone', 'email', 'website', 'established_year'),
        }),
        ("Ijtimoiy tarmoqlar", {
            'fields': ('telegram', 'instagram', 'facebook', 'youtube'),
            'classes': ('collapse',),
        }),
        ("Media", {
            'fields': ('logo', 'logo_preview'),
        }),
    )
    readonly_fields = ['logo_preview']

    def logo_preview(self, obj):
        if obj and obj.logo:
            return format_html(
                '<img src="{}" style="height:60px;border-radius:6px;border:1px solid #ddd;" />',
                obj.logo.url,
            )
        return mark_safe('<span style="color:#999">Logo yuklanmagan</span>')
    logo_preview.short_description = "Logo ko'rinishi"

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        form.base_fields['short_name_uz'].required = True
        form.base_fields['full_name_uz'].required = True
        return form
