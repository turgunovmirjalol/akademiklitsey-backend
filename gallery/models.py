from django.db import models
from django.utils.text import slugify


class GalleryAlbum(models.Model):
    """Galereya albomlari — title va description ko'p tilli."""

    # Tarjima maydonlari
    title_uz = models.CharField(max_length=300, blank=True, verbose_name="Nomi (UZ)")
    title_uz_cyrl = models.CharField(max_length=300, blank=True, verbose_name="Nomi (UZ Kirill)")
    title_ru = models.CharField(max_length=300, blank=True, verbose_name="Nomi (RU)")
    title_en = models.CharField(max_length=300, blank=True, verbose_name="Nomi (EN)")

    description_uz = models.TextField(null=True, blank=True, verbose_name="Tavsif (UZ)")
    description_uz_cyrl = models.TextField(null=True, blank=True, verbose_name="Tavsif (UZ Kirill)")
    description_ru = models.TextField(null=True, blank=True, verbose_name="Tavsif (RU)")
    description_en = models.TextField(null=True, blank=True, verbose_name="Tavsif (EN)")

    # Umumiy maydonlar
    slug = models.SlugField(max_length=350, unique=True, blank=True, verbose_name="Slug")
    cover_image = models.ImageField(
        upload_to='gallery_covers/', null=True, blank=True, verbose_name="Muqova rasmi"
    )
    event_date = models.DateField(null=True, blank=True, verbose_name="Tadbir sanasi")
    photos_count = models.PositiveIntegerField(default=0, verbose_name="Rasmlar soni")
    is_active = models.BooleanField(default=True, verbose_name="Faol")
    sort_order = models.IntegerField(default=0, verbose_name="Tartib")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Yaratilgan vaqt")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Yangilangan vaqt")

    class Meta:
        db_table = 'gallery_albums'
        verbose_name = "Galereya albomi"
        verbose_name_plural = "Galereya albomlari"
        ordering = ['sort_order', '-created_at']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['is_active', 'sort_order']),
            models.Index(fields=['event_date']),
        ]

    def __str__(self):
        return self.title_uz or self.title_ru or self.title_en or f"Album #{self.pk}"

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.title_uz or self.title_ru or self.title_en or 'album') or 'album'
            slug = base
            counter = 1
            while GalleryAlbum.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def update_photos_count(self):
        """Rasmlar sonini qayta hisoblash."""
        self.photos_count = self.photos.count()
        GalleryAlbum.objects.filter(pk=self.pk).update(photos_count=self.photos_count)


class GalleryPhoto(models.Model):
    """Galereya rasmlari."""
    album = models.ForeignKey(
        GalleryAlbum, on_delete=models.CASCADE,
        related_name='photos', verbose_name="Album"
    )
    image = models.ImageField(upload_to='gallery_photos/', verbose_name="Asosiy rasm")
    thumbnail = models.ImageField(
        upload_to='gallery_thumbnails/', null=True, blank=True, verbose_name="Kichik rasm"
    )
    caption = models.CharField(max_length=500, null=True, blank=True, verbose_name="Izoh")
    sort_order = models.IntegerField(default=0, verbose_name="Tartib")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Yuklangan vaqt")

    class Meta:
        db_table = 'gallery_photos'
        verbose_name = "Galereya rasmi"
        verbose_name_plural = "Galereya rasmlari"
        ordering = ['sort_order', 'created_at']
        indexes = [
            models.Index(fields=['album', 'sort_order']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"{self.album} - #{self.pk}"

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        if is_new:
            self.album.update_photos_count()

    def delete(self, *args, **kwargs):
        album = self.album
        super().delete(*args, **kwargs)
        album.update_photos_count()


class InfrastructureItem(models.Model):
    """
    Litseyning moddiy-texnik bazasi — partalari, kompyuterlari va boshqa jihozlar.
    Har bir element rasm va ko'p tilli tavsifga ega.
    """

    # Tarjima maydonlari
    title_uz = models.CharField(max_length=300, blank=True, verbose_name="Nomi (UZ)")
    title_uz_cyrl = models.CharField(max_length=300, blank=True, verbose_name="Nomi (UZ Kirill)")
    title_ru = models.CharField(max_length=300, blank=True, verbose_name="Nomi (RU)")
    title_en = models.CharField(max_length=300, blank=True, verbose_name="Nomi (EN)")

    description_uz = models.TextField(blank=True, verbose_name="Tavsif (UZ)")
    description_uz_cyrl = models.TextField(blank=True, verbose_name="Tavsif (UZ Kirill)")
    description_ru = models.TextField(blank=True, verbose_name="Tavsif (RU)")
    description_en = models.TextField(blank=True, verbose_name="Tavsif (EN)")

    # Umumiy maydonlar
    image = models.ImageField(upload_to='infrastructure/', verbose_name="Rasm")
    sort_order = models.IntegerField(default=0, verbose_name="Tartib")
    is_active = models.BooleanField(default=True, verbose_name="Faol")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Yaratilgan vaqt")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Yangilangan vaqt")

    class Meta:
        db_table = 'infrastructure_items'
        verbose_name = "Moddiy-texnik baza elementi"
        verbose_name_plural = "Moddiy-texnik baza"
        ordering = ['sort_order', '-created_at']
        indexes = [
            models.Index(fields=['is_active', 'sort_order']),
        ]

    def __str__(self):
        return self.title_uz or self.title_ru or self.title_en or f"Infrastructure #{self.pk}"

class Video(models.Model):
    """Video lavhalar — title va description ko'p tilli."""

    title_uz = models.CharField(max_length=300, blank=True, verbose_name="Sarlavha (UZ)")
    title_uz_cyrl = models.CharField(max_length=300, blank=True, verbose_name="Sarlavha (UZ Kirill)")
    title_ru = models.CharField(max_length=300, blank=True, verbose_name="Sarlavha (RU)")
    title_en = models.CharField(max_length=300, blank=True, verbose_name="Sarlavha (EN)")

    description_uz = models.TextField(blank=True, verbose_name="Tavsif (UZ)")
    description_uz_cyrl = models.TextField(blank=True, verbose_name="Tavsif (UZ Kirill)")
    description_ru = models.TextField(blank=True, verbose_name="Tavsif (RU)")
    description_en = models.TextField(blank=True, verbose_name="Tavsif (EN)")

    video_file = models.FileField(
        upload_to='videos/', verbose_name="Video fayl (mp4, webm va boshqalar)"
    )
    thumbnail = models.ImageField(
        upload_to='video_thumbnails/', null=True, blank=True, verbose_name="Muqova rasmi"
    )
    sort_order = models.IntegerField(default=0, verbose_name="Tartib")
    is_active = models.BooleanField(default=True, verbose_name="Faol")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Yaratilgan vaqt")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Yangilangan vaqt")

    class Meta:
        db_table = 'gallery_videos'
        verbose_name = "Video lavha"
        verbose_name_plural = "Video lavhalar"
        ordering = ['sort_order', '-created_at']
        indexes = [
            models.Index(fields=['is_active', 'sort_order']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return self.title_uz or self.title_ru or self.title_en or f"Video #{self.pk}"


class UsefulLink(models.Model):
    """Foydali havolalar."""
    name = models.CharField(max_length=200, verbose_name="Nomi")
    url = models.URLField(max_length=500, verbose_name="Havola")
    logo = models.ImageField(
        upload_to='useful_links_logos/', null=True, blank=True, verbose_name="Logo"
    )
    description = models.CharField(
        max_length=300, null=True, blank=True, verbose_name="Qisqa tavsif"
    )
    sort_order = models.IntegerField(default=0, verbose_name="Tartib")
    is_active = models.BooleanField(default=True, verbose_name="Faol")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Yaratilgan vaqt")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Yangilangan vaqt")

    class Meta:
        db_table = 'useful_links'
        verbose_name = "Foydali havola"
        verbose_name_plural = "Foydali havolalar"
        ordering = ['sort_order', 'name']
        indexes = [
            models.Index(fields=['is_active', 'sort_order']),
        ]

    def __str__(self):
        return self.name
