from django.db import models
from django.utils.text import slugify


class Circle(models.Model):
    class Category(models.TextChoices):
        SPORT = 'sport', 'Sport'
        ART = 'art', "San'at"
        SCIENCE = 'science', 'Fan'
        LANGUAGE = 'language', 'Til'
        TECH = 'tech', 'Texnologiya'
        OTHER = 'other', 'Boshqa'

    # Tarjima maydonlari
    name_uz = models.CharField(max_length=200, blank=True, verbose_name="Nomi (UZ)")
    name_uz_cyrl = models.CharField(max_length=200, blank=True, verbose_name="Nomi (UZ Kirill)")
    name_ru = models.CharField(max_length=200, blank=True, verbose_name="Nomi (RU)")
    name_en = models.CharField(max_length=200, blank=True, verbose_name="Nomi (EN)")

    description_uz = models.TextField(null=True, blank=True, verbose_name="Tavsif (UZ)")
    description_uz_cyrl = models.TextField(null=True, blank=True, verbose_name="Tavsif (UZ Kirill)")
    description_ru = models.TextField(null=True, blank=True, verbose_name="Tavsif (RU)")
    description_en = models.TextField(null=True, blank=True, verbose_name="Tavsif (EN)")

    schedule_uz = models.CharField(max_length=300, null=True, blank=True, verbose_name="Dars vaqti (UZ)")
    schedule_uz_cyrl = models.CharField(max_length=300, null=True, blank=True, verbose_name="Dars vaqti (UZ Kirill)")
    schedule_ru = models.CharField(max_length=300, null=True, blank=True, verbose_name="Dars vaqti (RU)")
    schedule_en = models.CharField(max_length=300, null=True, blank=True, verbose_name="Dars vaqti (EN)")

    # Umumiy maydonlar
    slug = models.SlugField(max_length=250, unique=True, blank=True, verbose_name="Slug")
    category = models.CharField(
        max_length=20, choices=Category.choices,
        default=Category.OTHER, verbose_name="Kategoriya"
    )
    teacher = models.ForeignKey(
        'structure.Teacher', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='circles', verbose_name="Rahbar o'qituvchi"
    )
    max_students = models.PositiveIntegerField(null=True, blank=True, verbose_name="Maksimal o'rinlar")
    current_students = models.PositiveIntegerField(default=0, verbose_name="Hozirgi o'quvchilar soni")
    room = models.CharField(max_length=50, null=True, blank=True, verbose_name="Xona")
    photo = models.ImageField(upload_to='circles/', null=True, blank=True, verbose_name="Rasm")
    is_active = models.BooleanField(default=True, verbose_name="Faolmi")
    sort_order = models.IntegerField(default=0, verbose_name="Tartib")

    class Meta:
        db_table = 'circles'
        verbose_name = "To'garak"
        verbose_name_plural = "To'garaklar"
        ordering = ['sort_order']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['category', 'is_active']),
            models.Index(fields=['is_active', 'sort_order']),
        ]

    def __str__(self):
        return self.name_uz or self.name_ru or self.name_en or f"Circle #{self.pk}"

    def get_name(self, lang='uz'):
        return getattr(self, f'name_{lang.replace("-", "_")}', '') or self.name_uz or ''

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.name_uz or self.name_ru or self.name_en or 'circle') or 'circle'
            slug = base
            counter = 1
            while Circle.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    @property
    def available_slots(self):
        if self.max_students is None:
            return None
        return max(0, self.max_students - self.current_students)

    @property
    def is_full(self):
        if self.max_students is None:
            return False
        return self.current_students >= self.max_students
