from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Department(models.Model):
    name = models.CharField(max_length=200, verbose_name="Kafedra nomi")
    slug = models.SlugField(max_length=250, unique=True, verbose_name="Slug")
    description = models.TextField(null=True, blank=True, verbose_name="Tavsif")

    # Circular FK -> Teachers, shuning uchun string reference ishlatiladi
    head_teacher = models.ForeignKey(
        'Teacher',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='headed_departments',
        verbose_name="Kafedra mudiri"
    )

    subjects = models.JSONField(
        null=True,
        blank=True,
        default=list,
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
        ordering = ['sort_order', 'name']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['is_active', 'sort_order']),
        ]

    def __str__(self):
        return self.name

    @property
    def teachers_count(self):
        return self.teachers.filter(is_active=True).count()


class Teacher(models.Model):
    class Category(models.TextChoices):
        HIGHEST = 'highest', 'Oliy toifa'
        FIRST = 'first', 'Birinchi toifa'
        SECOND = 'second', 'Ikkinchi toifa'
        NONE = 'none', 'Toifasiz'

    full_name = models.CharField(max_length=200, verbose_name="To'liq ismi")
    slug = models.SlugField(max_length=250, unique=True, verbose_name="Slug")
    position = models.CharField(max_length=200, verbose_name="Lavozimi")
    academic_degree = models.CharField(
        max_length=100,
        null=True, blank=True,
        verbose_name="Ilmiy daraja"
    )
    academic_rank = models.CharField(
        max_length=100,
        null=True, blank=True,
        verbose_name="Ilmiy unvon"
    )
    category = models.CharField(
        max_length=10,
        choices=Category.choices,
        default=Category.NONE,
        verbose_name="Toifa"
    )
    experience_years = models.PositiveIntegerField(
        null=True, blank=True,
        verbose_name="Ish staji (yil)"
    )
    subject = models.CharField(max_length=200, verbose_name="O'qitadigan fan")
    department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='teachers',
        verbose_name="Kafedra"
    )
    photo = models.ImageField(upload_to='teacher_photos/', null=True, blank=True, verbose_name="Rasm")
    bio = models.TextField(null=True, blank=True, verbose_name="Tarjimai hol")
    achievements = models.TextField(null=True, blank=True, verbose_name="Yutuqlar")
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
    @property
    def photo_url(self):
        """Rasm URL ni olish"""
        if self.photo:
            return self.photo.url
        return None


class Management(models.Model):
    full_name = models.CharField(max_length=200, verbose_name="To'liq ismi")
    position = models.CharField(max_length=200, verbose_name="Lavozimi")
    academic_degree = models.CharField(
        max_length=100,
        null=True, blank=True,
        verbose_name="Ilmiy daraja"
    )
    phone = models.CharField(max_length=20, null=True, blank=True, verbose_name="Telefon")
    email = models.EmailField(max_length=150, null=True, blank=True, verbose_name="Email")
    reception_hours = models.CharField(
        max_length=200,
        null=True, blank=True,
        verbose_name="Qabul vaqti"
    )
    photo = models.ImageField(upload_to='management_photos/', null=True, blank=True, verbose_name="Rasm")
    bio = models.TextField(null=True, blank=True, verbose_name="Tarjimai hol")
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
        return f"{self.full_name} - {self.position}"
    
    @property
    def photo_url(self):
        """Rasm URL ni olish"""
        if self.photo:
            return self.photo.url
        return None
