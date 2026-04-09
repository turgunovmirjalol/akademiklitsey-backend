from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.utils.text import slugify

User = get_user_model()

LANGS = ('uz', 'uz_cyrl', 'ru', 'en')


class News(models.Model):
    class Status(models.TextChoices):
        PUBLISHED = 'published', 'Published'
        DRAFT = 'draft', 'Draft'
        ARCHIVED = 'archived', 'Archived'

    # Tarjima maydonlari
    title_uz = models.CharField(max_length=300, blank=True, verbose_name="Sarlavha (UZ)")
    title_uz_cyrl = models.CharField(max_length=300, blank=True, verbose_name="Sarlavha (UZ Kirill)")
    title_ru = models.CharField(max_length=300, blank=True, verbose_name="Sarlavha (RU)")
    title_en = models.CharField(max_length=300, blank=True, verbose_name="Sarlavha (EN)")

    short_description_uz = models.TextField(blank=True, verbose_name="Qisqa tavsif (UZ)")
    short_description_uz_cyrl = models.TextField(blank=True, verbose_name="Qisqa tavsif (UZ Kirill)")
    short_description_ru = models.TextField(blank=True, verbose_name="Qisqa tavsif (RU)")
    short_description_en = models.TextField(blank=True, verbose_name="Qisqa tavsif (EN)")

    content_uz = models.TextField(blank=True, verbose_name="Matn (UZ)")
    content_uz_cyrl = models.TextField(blank=True, verbose_name="Matn (UZ Kirill)")
    content_ru = models.TextField(blank=True, verbose_name="Matn (RU)")
    content_en = models.TextField(blank=True, verbose_name="Matn (EN)")

    # Umumiy maydonlar
    slug = models.SlugField(max_length=350, unique=True, blank=True, verbose_name="Slug")
    image = models.ImageField(upload_to='news_images/', blank=True, null=True, verbose_name="Asosiy rasm")
    views_count = models.PositiveIntegerField(default=0, verbose_name="Ko'rishlar soni")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT, verbose_name="Holat")
    is_featured = models.BooleanField(default=False, verbose_name="Bosh sahifaga chiqarish")
    published_at = models.DateTimeField(null=True, blank=True, verbose_name="Nashr sanasi")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Yaratilgan vaqt")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Yangilangan vaqt")
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='news_created', verbose_name="Kim qo'shgan"
    )

    class Meta:
        db_table = 'news'
        verbose_name = "Yangilik"
        verbose_name_plural = "Yangiliklar"
        ordering = ['-published_at', '-created_at']
        indexes = [
            models.Index(fields=['status', 'is_featured']),
            models.Index(fields=['slug']),
            models.Index(fields=['-published_at']),
        ]

    def __str__(self):
        return self.title_uz or self.title_ru or self.title_en or f"News #{self.pk}"

    def get_title(self, lang='uz'):
        return getattr(self, f'title_{lang.replace("-", "_")}', '') or self.title_uz or ''

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.title_uz or self.title_ru or self.title_en or 'news') or 'news'
            slug = base
            counter = 1
            while News.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base}-{counter}"
                counter += 1
            self.slug = slug
        if self.status == self.Status.PUBLISHED and not self.published_at:
            self.published_at = timezone.now()
        super().save(*args, **kwargs)

    def increment_views(self):
        News.objects.filter(pk=self.pk).update(views_count=models.F('views_count') + 1)


class Announcement(models.Model):
    class Status(models.TextChoices):
        PUBLISHED = 'published', 'Published'
        DRAFT = 'draft', 'Draft'
        ARCHIVED = 'archived', 'Archived'

    # Tarjima maydonlari
    title_uz = models.CharField(max_length=300, blank=True, verbose_name="Sarlavha (UZ)")
    title_uz_cyrl = models.CharField(max_length=300, blank=True, verbose_name="Sarlavha (UZ Kirill)")
    title_ru = models.CharField(max_length=300, blank=True, verbose_name="Sarlavha (RU)")
    title_en = models.CharField(max_length=300, blank=True, verbose_name="Sarlavha (EN)")

    short_description_uz = models.TextField(blank=True, verbose_name="Qisqa tavsif (UZ)")
    short_description_uz_cyrl = models.TextField(blank=True, verbose_name="Qisqa tavsif (UZ Kirill)")
    short_description_ru = models.TextField(blank=True, verbose_name="Qisqa tavsif (RU)")
    short_description_en = models.TextField(blank=True, verbose_name="Qisqa tavsif (EN)")

    content_uz = models.TextField(blank=True, verbose_name="Matn (UZ)")
    content_uz_cyrl = models.TextField(blank=True, verbose_name="Matn (UZ Kirill)")
    content_ru = models.TextField(blank=True, verbose_name="Matn (RU)")
    content_en = models.TextField(blank=True, verbose_name="Matn (EN)")

    # Umumiy maydonlar
    slug = models.SlugField(max_length=350, unique=True, blank=True, verbose_name="Slug")
    image = models.ImageField(upload_to='announcement_images/', blank=True, null=True, verbose_name="Asosiy rasm")
    views_count = models.PositiveIntegerField(default=0, verbose_name="Ko'rishlar soni")
    is_important = models.BooleanField(default=False, verbose_name="Muhim e'lon")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT, verbose_name="Holat")
    expires_at = models.DateTimeField(null=True, blank=True, verbose_name="Muddati tugash sanasi")
    published_at = models.DateTimeField(null=True, blank=True, verbose_name="Nashr sanasi")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Yaratilgan vaqt")
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='announcements_created', verbose_name="Kim qo'shgan"
    )

    class Meta:
        db_table = 'announcements'
        verbose_name = "E'lon"
        verbose_name_plural = "E'lonlar"
        ordering = ['-published_at', '-created_at']
        indexes = [
            models.Index(fields=['status', 'is_important']),
            models.Index(fields=['slug']),
            models.Index(fields=['-published_at']),
            models.Index(fields=['expires_at']),
        ]

    def __str__(self):
        return self.title_uz or self.title_ru or self.title_en or f"Announcement #{self.pk}"

    def get_title(self, lang='uz'):
        return getattr(self, f'title_{lang.replace("-", "_")}', '') or self.title_uz or ''

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.title_uz or self.title_ru or self.title_en or 'announcement') or 'announcement'
            slug = base
            counter = 1
            while Announcement.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base}-{counter}"
                counter += 1
            self.slug = slug
        if self.status == self.Status.PUBLISHED and not self.published_at:
            self.published_at = timezone.now()
        super().save(*args, **kwargs)

    @property
    def is_expired(self):
        if self.expires_at:
            return timezone.now() > self.expires_at
        return False
