from django.contrib import admin
from django.utils.html import format_html
from .models import Statistic


@admin.register(Statistic)
class StatisticAdmin(admin.ModelAdmin):
    list_display = ['label_badge', 'key', 'value_badge', 'icon_preview', 'sort_order', 'updated_at']
    list_filter = ['sort_order']
    search_fields = ['key', 'label_uz', 'label_ru', 'label_en']
    list_editable = ['sort_order']
    ordering = ['sort_order']
    readonly_fields = ['updated_at']

    fieldsets = (
        ("O'zbek tili (Lotin)", {
            'fields': ('label_uz',),
            'description': "Asosiy til — kamida shu til to'ldirilishi shart.",
        }),
        ("O'zbek tili (Kirill)", {
            'fields': ('label_uz_cyrl',),
            'classes': ('collapse',),
        }),
        ("Rus tili", {
            'fields': ('label_ru',),
            'classes': ('collapse',),
        }),
        ("Ingliz tili", {
            'fields': ('label_en',),
            'classes': ('collapse',),
        }),
        ("Asosiy ma'lumotlar", {
            'fields': ('key', 'value', 'icon', 'sort_order'),
        }),
        ("Tizim", {
            'fields': ('updated_at',),
            'classes': ('collapse',),
        }),
    )

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        form.base_fields['label_uz'].required = True
        return form

    def label_badge(self, obj):
        label = obj.label_uz or obj.label_ru or obj.label_en or '—'
        return format_html('<strong>{}</strong>', label)
    label_badge.short_description = "Yorliq"

    def value_badge(self, obj):
        return format_html(
            '<span style="background:#007bff;color:#fff;padding:2px 10px;'
            'border-radius:4px;font-weight:bold">{}</span>',
            obj.value,
        )
    value_badge.short_description = "Qiymat"

    def icon_preview(self, obj):
        if obj.icon:
            return format_html('<i class="{}" style="font-size:18px"></i> <code>{}</code>', obj.icon, obj.icon)
        return '—'
    icon_preview.short_description = "Icon"
