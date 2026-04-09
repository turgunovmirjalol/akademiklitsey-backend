from django.contrib import admin
from django.utils.html import format_html
from .models import GalleryAlbum, GalleryPhoto, UsefulLink


class GalleryPhotoInline(admin.TabularInline):
    model = GalleryPhoto
    extra = 1
    fields = ['image', 'thumbnail', 'caption', 'sort_order']
    ordering = ['sort_order']
    readonly_fields = ['created_at']


@admin.register(GalleryAlbum)
class GalleryAlbumAdmin(admin.ModelAdmin):
    list_display = ['title_badge', 'photos_count', 'event_date', 'is_active', 'sort_order']
    list_filter = ['is_active', 'event_date']
    search_fields = ['title_uz', 'title_ru', 'title_en', 'description_uz']
    list_editable = ['is_active', 'sort_order']
    ordering = ['sort_order', '-created_at']
    readonly_fields = ['photos_count', 'created_at', 'updated_at', 'slug']
    inlines = [GalleryPhotoInline]

    fieldsets = (
        ("O'zbek tili (Lotin)", {
            'fields': ('title_uz', 'description_uz'),
            'description': "Asosiy til — kamida shu til to'ldirilishi shart.",
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
        ("Media", {
            'fields': ('cover_image',),
        }),
        ("Sozlamalar", {
            'fields': ('slug', 'event_date', 'is_active', 'sort_order'),
        }),
        ("Tizim", {
            'fields': ('photos_count', 'created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        form.base_fields['title_uz'].required = True
        return form

    def get_readonly_fields(self, request, obj=None):
        base = ['photos_count', 'created_at', 'updated_at']
        if obj:
            base.append('slug')
        return base

    def title_badge(self, obj):
        title = obj.title_uz or obj.title_ru or obj.title_en or '—'
        return format_html('<strong>{}</strong>', title)
    title_badge.short_description = "Nomi"

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('photos')


@admin.register(GalleryPhoto)
class GalleryPhotoAdmin(admin.ModelAdmin):
    list_display = ['photo_preview', 'album', 'caption', 'sort_order', 'created_at']
    list_filter = ['album', 'created_at']
    search_fields = ['caption', 'album__title_uz', 'album__title_ru']
    list_editable = ['sort_order']
    ordering = ['album', 'sort_order']
    readonly_fields = ['created_at', 'photo_preview']

    def photo_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="height:50px;border-radius:4px;" />',
                obj.image.url,
            )
        return '—'
    photo_preview.short_description = "Rasm"

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('album')


@admin.register(UsefulLink)
class UsefulLinkAdmin(admin.ModelAdmin):
    list_display = ['logo_preview', 'name', 'url_short', 'is_active', 'sort_order']
    list_filter = ['is_active']
    search_fields = ['name', 'description']
    list_editable = ['is_active', 'sort_order']
    ordering = ['sort_order', 'name']
    readonly_fields = ['logo_preview', 'created_at', 'updated_at']

    fieldsets = (
        ("Asosiy ma'lumotlar", {
            'fields': ('name', 'url', 'description'),
        }),
        ("Media", {
            'fields': ('logo', 'logo_preview'),
        }),
        ("Sozlamalar", {
            'fields': ('is_active', 'sort_order'),
        }),
        ("Tizim", {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    def logo_preview(self, obj):
        if obj.logo:
            return format_html(
                '<img src="{}" style="height:40px;border-radius:4px;" />',
                obj.logo.url,
            )
        return '—'
    logo_preview.short_description = "Logo"

    def url_short(self, obj):
        return format_html('<a href="{}" target="_blank">{}</a>', obj.url, obj.url[:40] + '...' if len(obj.url) > 40 else obj.url)
    url_short.short_description = "URL"
