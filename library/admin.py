from django.contrib import admin
from django.utils.html import format_html, mark_safe
from .models import LibraryResource, LibraryStats


@admin.register(LibraryStats)
class LibraryStatsAdmin(admin.ModelAdmin):
    list_display = [
        'books_count', 'electronic_resources_count',
        'journals_count', 'manuals_count', 'updated_at',
    ]
    readonly_fields = ['updated_at']

    fieldsets = (
        ("Kitoblar", {'fields': ('books_count', 'books_suffix')}),
        ("Elektron resurslar", {'fields': ('electronic_resources_count', 'electronic_resources_suffix')}),
        ("Jurnallar", {'fields': ('journals_count', 'journals_suffix')}),
        ("O'quv qo'llanmalari", {'fields': ('manuals_count', 'manuals_suffix')}),
        ("Tizim", {'fields': ('updated_at',), 'classes': ('collapse',)}),
    )

    def has_add_permission(self, request):
        # Singleton: faqat bitta yozuv bo'lishi kerak
        return not LibraryStats.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(LibraryResource)
class LibraryResourceAdmin(admin.ModelAdmin):
    list_display = [
        '__str__', 'author', 'category', 'file_type',
        'is_featured', 'is_active', 'download_count', 'sort_order', 'cover_preview',
    ]
    list_filter = ['category', 'file_type', 'is_featured', 'is_active']
    search_fields = ['title_uz', 'title_ru', 'title_en', 'author']
    list_editable = ['is_featured', 'is_active', 'sort_order']
    ordering = ['sort_order', '-created_at']
    readonly_fields = ['download_count', 'created_at', 'updated_at', 'cover_preview']

    fieldsets = (
        ("O'zbek tili (Lotin)", {
            'fields': ('title_uz', 'description_uz'),
        }),
        ("O'zbek tili (Kirill)", {
            'fields': ('title_uz_cyrl', 'description_uz_cyrl'),
            'classes': ('collapse',),
        }),
        ("Rus tili", {
            'fields': ('title_ru', 'description_ru'),
            'classes': ('collapse',),
        }),
        ("Ingliz tili", {
            'fields': ('title_en', 'description_en'),
            'classes': ('collapse',),
        }),
        ("Asosiy ma'lumotlar", {
            'fields': ('author', 'category', 'file_type', 'file', 'cover_image', 'cover_preview'),
        }),
        ("Sozlamalar", {
            'fields': ('is_featured', 'is_active', 'sort_order', 'download_count'),
        }),
        ("Tizim", {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    def cover_preview(self, obj):
        if obj.cover_image:
            return mark_safe(
                f'<img src="{obj.cover_image.url}" style="max-height:80px;border-radius:4px;" />'
            )
        return '—'
    cover_preview.short_description = "Muqova"

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        form.base_fields['title_uz'].required = True
        return form
