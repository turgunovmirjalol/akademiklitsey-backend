from django.contrib import admin
from django.utils.html import format_html
from .models import Department, Teacher, Management


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ['name_badge', 'head_teacher', 'teachers_count_badge', 'room_number', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name_uz', 'name_ru', 'name_en', 'description_uz']
    list_editable = ['is_active']
    ordering = ['sort_order', 'name_uz']
    readonly_fields = ['created_at', 'slug', 'teachers_count_badge']

    fieldsets = (
        ("O'zbek tili (Lotin)", {
            'fields': ('name_uz', 'description_uz'),
            'description': "Asosiy til — kamida shu til to'ldirilishi shart.",
        }),
        ("O'zbek tili (Kirill)", {
            'fields': ('name_uz_cyrl', 'description_uz_cyrl'),
            'classes': ('collapse',),
        }),
        ("Rus tili", {
            'fields': ('name_ru', 'description_ru'),
            'classes': ('collapse',),
        }),
        ("Ingliz tili", {
            'fields': ('name_en', 'description_en'),
            'classes': ('collapse',),
        }),
        ("Kafedra ma'lumotlari", {
            'fields': ('slug', 'head_teacher', 'subjects', 'room_number', 'phone', 'email'),
        }),
        ("Sozlamalar", {
            'fields': ('sort_order', 'is_active'),
        }),
        ("Tizim", {
            'fields': ('created_at', 'teachers_count_badge'),
            'classes': ('collapse',),
        }),
    )

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        form.base_fields['name_uz'].required = True
        return form

    def get_readonly_fields(self, request, obj=None):
        base = ['created_at', 'teachers_count_badge']
        if obj:
            base.append('slug')
        return base

    def name_badge(self, obj):
        name = obj.name_uz or obj.name_ru or obj.name_en or '—'
        return format_html('<strong>{}</strong>', name)
    name_badge.short_description = "Nomi"

    def teachers_count_badge(self, obj):
        if not obj.pk:
            return '—'
        count = obj.teachers_count
        color = '#28a745' if count > 0 else '#6c757d'
        return format_html(
            '<span style="background:{};color:#fff;padding:2px 8px;border-radius:4px">{} o\'qituvchi</span>',
            color, count,
        )
    teachers_count_badge.short_description = "O'qituvchilar"


@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ['photo_preview', 'full_name', 'department', 'category_badge', 'experience_years', 'is_active']
    list_filter = ['category', 'department', 'is_active']
    search_fields = ['full_name', 'position_uz', 'position_ru', 'subject_uz', 'email']
    list_editable = ['is_active']
    ordering = ['sort_order', 'full_name']
    readonly_fields = ['created_at', 'slug', 'photo_preview']

    fieldsets = (
        ("Asosiy ma'lumotlar", {
            'fields': ('full_name', 'slug', 'photo', 'photo_preview', 'department', 'category', 'experience_years', 'academic_degree', 'academic_rank', 'email'),
        }),
        ("Lavozim (O'zbek lotin)", {
            'fields': ('position_uz', 'subject_uz'),
            'description': "Asosiy til — kamida shu til to'ldirilishi shart.",
        }),
        ("Lavozim (O'zbek kirill)", {
            'fields': ('position_uz_cyrl', 'subject_uz_cyrl'),
            'classes': ('collapse',),
        }),
        ("Lavozim (Rus)", {
            'fields': ('position_ru', 'subject_ru'),
            'classes': ('collapse',),
        }),
        ("Lavozim (Ingliz)", {
            'fields': ('position_en', 'subject_en'),
            'classes': ('collapse',),
        }),
        ("Tarjimai hol (O'zbek lotin)", {
            'fields': ('bio_uz', 'achievements_uz'),
            'classes': ('collapse',),
        }),
        ("Tarjimai hol (O'zbek kirill)", {
            'fields': ('bio_uz_cyrl', 'achievements_uz_cyrl'),
            'classes': ('collapse',),
        }),
        ("Tarjimai hol (Rus)", {
            'fields': ('bio_ru', 'achievements_ru'),
            'classes': ('collapse',),
        }),
        ("Tarjimai hol (Ingliz)", {
            'fields': ('bio_en', 'achievements_en'),
            'classes': ('collapse',),
        }),
        ("Sozlamalar", {
            'fields': ('sort_order', 'is_active'),
        }),
        ("Tizim", {
            'fields': ('created_at',),
            'classes': ('collapse',),
        }),
    )

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        form.base_fields['position_uz'].required = True
        return form

    def get_readonly_fields(self, request, obj=None):
        base = ['created_at', 'photo_preview']
        if obj:
            base.append('slug')
        return base

    def photo_preview(self, obj):
        if obj and obj.photo:
            return format_html(
                '<img src="{}" style="height:50px;width:50px;border-radius:50%;object-fit:cover;" />',
                obj.photo.url,
            )
        return '—'
    photo_preview.short_description = "Rasm"

    def category_badge(self, obj):
        colors = {
            'highest': '#28a745', 'first': '#007bff',
            'second': '#fd7e14', 'none': '#6c757d',
        }
        color = colors.get(obj.category, '#6c757d')
        return format_html(
            '<span style="background:{};color:#fff;padding:2px 8px;border-radius:4px;font-size:11px">{}</span>',
            color, obj.get_category_display(),
        )
    category_badge.short_description = "Toifa"

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('department')


@admin.register(Management)
class ManagementAdmin(admin.ModelAdmin):
    list_display = ['photo_preview', 'full_name', 'position_badge', 'phone', 'is_active', 'sort_order']
    list_filter = ['is_active']
    search_fields = ['full_name', 'position_uz', 'position_ru', 'email']
    list_editable = ['is_active', 'sort_order']
    ordering = ['sort_order']
    readonly_fields = ['photo_preview']

    fieldsets = (
        ("Asosiy ma'lumotlar", {
            'fields': ('full_name', 'photo', 'photo_preview', 'academic_degree', 'phone', 'email'),
        }),
        ("Lavozim (O'zbek lotin)", {
            'fields': ('position_uz', 'reception_hours_uz'),
            'description': "Asosiy til — kamida shu til to'ldirilishi shart.",
        }),
        ("Lavozim (O'zbek kirill)", {
            'fields': ('position_uz_cyrl', 'reception_hours_uz_cyrl'),
            'classes': ('collapse',),
        }),
        ("Lavozim (Rus)", {
            'fields': ('position_ru', 'reception_hours_ru'),
            'classes': ('collapse',),
        }),
        ("Lavozim (Ingliz)", {
            'fields': ('position_en', 'reception_hours_en'),
            'classes': ('collapse',),
        }),
        ("Tarjimai hol (O'zbek lotin)", {
            'fields': ('bio_uz',),
            'classes': ('collapse',),
        }),
        ("Tarjimai hol (O'zbek kirill)", {
            'fields': ('bio_uz_cyrl',),
            'classes': ('collapse',),
        }),
        ("Tarjimai hol (Rus)", {
            'fields': ('bio_ru',),
            'classes': ('collapse',),
        }),
        ("Tarjimai hol (Ingliz)", {
            'fields': ('bio_en',),
            'classes': ('collapse',),
        }),
        ("Sozlamalar", {
            'fields': ('sort_order', 'is_active'),
        }),
    )

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        form.base_fields['position_uz'].required = True
        return form

    def photo_preview(self, obj):
        if obj and obj.photo:
            return format_html(
                '<img src="{}" style="height:50px;width:50px;border-radius:50%;object-fit:cover;" />',
                obj.photo.url,
            )
        return '—'
    photo_preview.short_description = "Rasm"

    def position_badge(self, obj):
        pos = obj.position_uz or obj.position_ru or '—'
        return format_html('<em>{}</em>', pos)
    position_badge.short_description = "Lavozimi"
