from django.contrib import admin
from django.utils.html import format_html
from .models import Circle


@admin.register(Circle)
class CircleAdmin(admin.ModelAdmin):
    list_display = [
        'name_badge', 'category_badge', 'teacher', 'students_info',
        'room', 'is_active', 'sort_order',
    ]
    list_filter = ['category', 'is_active']
    search_fields = ['name_uz', 'name_ru', 'name_en', 'description_uz']
    list_editable = ['is_active', 'sort_order']
    ordering = ['sort_order']
    readonly_fields = ['slug', 'available_slots_display']

    fieldsets = (
        ("O'zbek tili (Lotin)", {
            'fields': ('name_uz', 'description_uz', 'schedule_uz'),
            'description': "Asosiy til — kamida shu til to'ldirilishi shart.",
        }),
        ("O'zbek tili (Kirill)", {
            'fields': ('name_uz_cyrl', 'description_uz_cyrl', 'schedule_uz_cyrl'),
            'classes': ('collapse',),
        }),
        ("Rus tili", {
            'fields': ('name_ru', 'description_ru', 'schedule_ru'),
            'classes': ('collapse',),
        }),
        ("Ingliz tili", {
            'fields': ('name_en', 'description_en', 'schedule_en'),
            'classes': ('collapse',),
        }),
        ("Asosiy ma'lumotlar", {
            'fields': ('slug', 'category', 'teacher'),
        }),
        ("O'quvchilar", {
            'fields': ('max_students', 'current_students', 'available_slots_display', 'room'),
        }),
        ("Media va sozlamalar", {
            'fields': ('photo', 'is_active', 'sort_order'),
        }),
    )

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        form.base_fields['name_uz'].required = True
        return form

    def name_badge(self, obj):
        name = obj.name_uz or obj.name_ru or obj.name_en or '—'
        return format_html('<strong>{}</strong>', name)
    name_badge.short_description = "Nomi"

    def category_badge(self, obj):
        colors = {
            'sport': '#28a745', 'art': '#e83e8c', 'science': '#007bff',
            'language': '#fd7e14', 'tech': '#6f42c1', 'other': '#6c757d',
        }
        color = colors.get(obj.category, '#6c757d')
        return format_html(
            '<span style="background:{};color:#fff;padding:2px 8px;'
            'border-radius:4px;font-size:11px">{}</span>',
            color, obj.get_category_display(),
        )
    category_badge.short_description = "Kategoriya"

    def students_info(self, obj):
        if obj.max_students:
            pct = int((obj.current_students / obj.max_students) * 100)
            color = '#dc3545' if pct >= 90 else '#fd7e14' if pct >= 70 else '#28a745'
            return format_html(
                '<span style="color:{}">{}/{}</span>',
                color, obj.current_students, obj.max_students,
            )
        return format_html('<span>{} / —</span>', obj.current_students)
    students_info.short_description = "O'quvchilar"

    def available_slots_display(self, obj):
        if obj.max_students is None:
            return "Cheklanmagan"
        slots = obj.available_slots
        color = '#dc3545' if slots == 0 else '#28a745'
        label = "To'lgan" if slots == 0 else f"{slots} bo'sh o'rin"
        return format_html('<span style="color:{};font-weight:bold">{}</span>', color, label)
    available_slots_display.short_description = "Bo'sh o'rinlar"

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('teacher')
