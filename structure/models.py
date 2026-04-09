from django.db import models
from django.utils.text import slugify


class Department(models.Model):
    """Kafedra — name va description ko'p tilli."""

    # Tarjima maydonlari
    name_uz = models.CharField(max_length=200, blank=True, verbose_name="Nomi (UZ)")
    name_uz_cyrl = models.CharField(max_length=200, blank=True, verbose_name="Nomi (UZ Kirill)")
    name_ru = models.CharField(max_length=200, blank=True, verbose_name="Nomi (RU)")
    name_en = models.CharField(max_length=200, blank=True, verbose_name="Nomi (EN)")

    description_uz = models.TextField(null=True, blank=True, verbose_name="Tavsif (UZ)")
    description_uz_cyrl = models.TextField(null=True, blank=True, verbose_name="Tavsif (UZ Kirill)")
    description_ru = models.TextField(null=True, blank=True, verbose_name="Tavsif (RU)")
    description_en = models.TextField(null=True, blank=True, verbose_name="Tavsif (EN)")

    # Umumiy maydonlar
    slug = models.SlugField(max_length=250, unique=True, blank=True, verbose_name="Slug")
    head_teacher = models.ForeignKey(
        'Teacher', on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='headed_departments',
        verbose_name="Kafedra mudiri"
    )
    subjects = models.JSONField(
        null=True, blank=True, default=list,
        verbose_name="Fanlar ro'yxati"
    )
    room_number = models.CharField(max_length=20, null=True, blank=True, verbose_name="Xona raqami")
    phone = models.CharField(max_length=20, null=True, blank=True, verbose_name="Telefon")
    email = models.EmailField(max_length=150, null=True, blank=True, verbose_name="Email")
    sort_order = models.IntegerField(default=0, verbose_name="Tartib")
    is_active = models.BooleanField(default=True, verbose_name="Faolmi")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Yaratilgan vaqt")

    class Meta:
        db_table = 'departments'
        verbose_name = "Kafedra"
        verbose_name_plural = "Kafedralar"
        ordering = ['sort_order', 'name_uz']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['is_active', 'sort_order']),
        ]

    def __str__(self):
        return self.name_uz or self.name_ru or self.name_en or f"Department #{self.pk}"

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.name_uz or self.name_ru or self.name_en or 'department') or 'department'
            slug = base
            counter = 1
            while Department.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    @property
    def teachers_count(self):
        return self.teachers.filter(is_active=True).count()


class Teacher(models.Model):
    """O'qituvchi — position, bio, achievements, subject ko'p tilli."""

    class Category(models.TextChoices):
        HIGHEST = 'highest', 'Oliy toifa'
        FIRST = 'first', 'Birinchi toifa'
        SECOND = 'second', 'Ikkinchi toifa'
        NONE = 'none', 'Toifasiz'

    # Umumiy (tarjima talab qilmaydi)
    full_name = models.CharField(max_length=200, verbose_name="To'liq ismi")
    slug = models.SlugField(max_length=250, unique=True, blank=True, verbose_name="Slug")

    # Tarjima maydonlari
    position_uz = models.CharField(max_length=200, blank=True, verbose_name="Lavozimi (UZ)")
    position_uz_cyrl = models.CharField(max_length=200, blank=True, verbose_name="Lavozimi (UZ Kirill)")
    position_ru = models.CharField(max_length=200, blank=True, verbose_name="Lavozimi (RU)")
    position_en = models.CharField(max_length=200, blank=True, verbose_name="Lavozimi (EN)")

    subject_uz = models.CharField(max_length=200, blank=True, verbose_name="O'qitadigan fan (UZ)")
    subject_uz_cyrl = models.CharField(max_length=200, blank=True, verbose_name="O'qitadigan fan (UZ Kirill)")
    subject_ru = models.CharField(max_length=200, blank=True, verbose_name="O'qitadigan fan (RU)")
    subject_en = models.CharField(max_length=200, blank=True, verbose_name="O'qitadigan fan (EN)")

    bio_uz = models.TextField(null=True, blank=True, verbose_name="Tarjimai hol (UZ)")
    bio_uz_cyrl = models.TextField(null=True, blank=True, verbose_name="Tarjimai hol (UZ Kirill)")
    bio_ru = models.TextField(null=True, blank=True, verbose_name="Tarjimai hol (RU)")
    bio_en = models.TextField(null=True, blank=True, verbose_name="Tarjimai hol (EN)")

    achievements_uz = models.TextField(null=True, blank=True, verbose_name="Yutuqlar (UZ)")
    achievements_uz_cyrl = models.TextField(null=True, blank=True, verbose_name="Yutuqlar (UZ Kirill)")
    achievements_ru = models.TextField(null=True, blank=True, verbose_name="Yutuqlar (RU)")
    achievements_en = models.TextField(null=True, blank=True, verbose_name="Yutuqlar (EN)")

    # Umumiy maydonlar
    academic_degree = models.CharField(max_length=100, null=True, blank=True, verbose_name="Ilmiy daraja")
    academic_rank = models.CharField(max_length=100, null=True, blank=True, verbose_name="Ilmiy unvon")
    category = models.CharField(
        max_length=10, choices=Category.choices,
        default=Category.NONE, verbose_name="Toifa"
    )
    experience_years = models.PositiveIntegerField(null=True, blank=True, verbose_name="Ish staji (yil)")
    department = models.ForeignKey(
        Department, on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='teachers', verbose_name="Kafedra"
    )
    photo = models.ImageField(upload_to='teacher_photos/', null=True, blank=True, verbose_name="Rasm")
    email = models.EmailField(max_length=150, null=True, blank=True, verbose_name="Email")
    is_active = models.BooleanField(default=True, verbose_name="Faolmi")
    sort_order = models.IntegerField(default=0, verbose_name="Tartib")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Yaratilgan vaqt")

    class Meta:
        db_table = 'teachers'
        verbose_name = "O'qituvchi"
        verbose_name_plural = "O'qituvchilar"
        ordering = ['sort_order', 'full_name']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['department', 'is_active']),
            models.Index(fields=['category', 'is_active']),
        ]

    def __str__(self):
        return self.full_name

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.full_name or 'teacher') or 'teacher'
            slug = base
            counter = 1
            while Teacher.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)


class Management(models.Model):
    """Rahbariyat — position, bio, reception_hours ko'p tilli."""

    # Umumiy
    full_name = models.CharField(max_length=200, verbose_name="To'liq ismi")

    # Tarjima maydonlari
    position_uz = models.CharField(max_length=200, blank=True, verbose_name="Lavozimi (UZ)")
    position_uz_cyrl = models.CharField(max_length=200, blank=True, verbose_name="Lavozimi (UZ Kirill)")
    position_ru = models.CharField(max_length=200, blank=True, verbose_name="Lavozimi (RU)")
    position_en = models.CharField(max_length=200, blank=True, verbose_name="Lavozimi (EN)")

    bio_uz = models.TextField(null=True, blank=True, verbose_name="Tarjimai hol (UZ)")
    bio_uz_cyrl = models.TextField(null=True, blank=True, verbose_name="Tarjimai hol (UZ Kirill)")
    bio_ru = models.TextField(null=True, blank=True, verbose_name="Tarjimai hol (RU)")
    bio_en = models.TextField(null=True, blank=True, verbose_name="Tarjimai hol (EN)")

    reception_hours_uz = models.CharField(max_length=200, null=True, blank=True, verbose_name="Qabul vaqti (UZ)")
    reception_hours_uz_cyrl = models.CharField(max_length=200, null=True, blank=True, verbose_name="Qabul vaqti (UZ Kirill)")
    reception_hours_ru = models.CharField(max_length=200, null=True, blank=True, verbose_name="Qabul vaqti (RU)")
    reception_hours_en = models.CharField(max_length=200, null=True, blank=True, verbose_name="Qabul vaqti (EN)")

    # Umumiy maydonlar
    academic_degree = models.CharField(max_length=100, null=True, blank=True, verbose_name="Ilmiy daraja")
    phone = models.CharField(max_length=20, null=True, blank=True, verbose_name="Telefon")
    email = models.EmailField(max_length=150, null=True, blank=True, verbose_name="Email")
    photo = models.ImageField(upload_to='management_photos/', null=True, blank=True, verbose_name="Rasm")
    sort_order = models.IntegerField(default=0, verbose_name="Tartib")
    is_active = models.BooleanField(default=True, verbose_name="Faolmi")

    class Meta:
        db_table = 'management'
        verbose_name = "Rahbar"
        verbose_name_plural = "Rahbariyat"
        ordering = ['sort_order']
        indexes = [
            models.Index(fields=['is_active', 'sort_order']),
        ]

    def __str__(self):
        pos = self.position_uz or self.position_ru or ''
        return f"{self.full_name} — {pos}" if pos else self.full_name
