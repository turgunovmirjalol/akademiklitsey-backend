from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import date


class AdmissionInfo(models.Model):
    academic_year = models.CharField(max_length=20, verbose_name="O'quv yili")
    total_quota = models.PositiveIntegerField(verbose_name="Jami o'rinlar")
    grant_quota = models.PositiveIntegerField(verbose_name="Grant o'rinlari")
    contract_quota = models.PositiveIntegerField(verbose_name="Kontrakt o'rinlari")
    contract_price = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True,
        verbose_name="Kontrakt summasi (so'm)"
    )
    application_start = models.DateField(verbose_name="Ariza qabul boshlanishi")
    application_end = models.DateField(verbose_name="Ariza qabul tugashi")
    exam_date = models.DateField(null=True, blank=True, verbose_name="Imtihon sanasi")
    results_date = models.DateField(null=True, blank=True, verbose_name="Natijalar e'lon qilinish sanasi")
    online_apply_url = models.CharField(max_length=500, null=True, blank=True, verbose_name="Onlayn ariza havolasi")
    is_active = models.BooleanField(default=True, verbose_name="Joriy yil ma'lumoti")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Yaratilgan vaqt")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Yangilangan vaqt")

    class Meta:
        db_table = 'admission_info'
        verbose_name = "Qabul ma'lumoti"
        verbose_name_plural = "Qabul ma'lumotlari"
        ordering = ['-academic_year']
        indexes = [
            models.Index(fields=['academic_year'], name='adm_info_year_idx'),
            models.Index(fields=['is_active'], name='adm_info_active_idx'),
        ]

    def __str__(self):
        return f"{self.academic_year} - Qabul"

    def clean(self):
        super().clean()
        if not self.pk:
            current_year = timezone.now().year
            try:
                year_part = int(self.academic_year.split('-')[0])
                if year_part != current_year:
                    raise ValidationError({
                        'academic_year': f"O'quv yili joriy yil ({current_year}) bo'lishi kerak."
                    })
            except (ValueError, IndexError):
                raise ValidationError({
                    'academic_year': "O'quv yili noto'g'ri formatda. Masalan: 2024-2025."
                })
        if self.is_active:
            if AdmissionInfo.objects.filter(is_active=True).exclude(pk=self.pk).exists():
                raise ValidationError({
                    'is_active': "Faol bo'lgan boshqa qabul ma'lumoti mavjud. Avval uni nofaol qiling."
                })

    def save(self, *args, **kwargs):
        if self.is_active and self.application_end and self.application_end < date.today():
            self.is_active = False
        if self.is_active:
            AdmissionInfo.objects.filter(is_active=True).exclude(pk=self.pk).update(is_active=False)
        super().save(*args, **kwargs)

    @classmethod
    def deactivate_expired(cls):
        cls.objects.filter(is_active=True, application_end__lt=date.today()).update(is_active=False)


class AdmissionSubject(models.Model):
    class SubjectType(models.TextChoices):
        TEST = 'test', 'Test'
        ESSAY = 'essay', 'Insho'
        INTERVIEW = 'interview', 'Intervyu'

    # Tarjima maydonlari
    subject_name_uz = models.CharField(max_length=200, blank=True, verbose_name="Fan nomi (UZ)")
    subject_name_uz_cyrl = models.CharField(max_length=200, blank=True, verbose_name="Fan nomi (UZ Kirill)")
    subject_name_ru = models.CharField(max_length=200, blank=True, verbose_name="Fan nomi (RU)")
    subject_name_en = models.CharField(max_length=200, blank=True, verbose_name="Fan nomi (EN)")

    description_uz = models.TextField(null=True, blank=True, verbose_name="Tavsif (UZ)")
    description_uz_cyrl = models.TextField(null=True, blank=True, verbose_name="Tavsif (UZ Kirill)")
    description_ru = models.TextField(null=True, blank=True, verbose_name="Tavsif (RU)")
    description_en = models.TextField(null=True, blank=True, verbose_name="Tavsif (EN)")

    subject_type = models.CharField(
        max_length=20, choices=SubjectType.choices,
        default=SubjectType.TEST, verbose_name="Fan turi"
    )
    max_score = models.PositiveIntegerField(verbose_name="Maksimal ball")
    sort_order = models.IntegerField(default=0, verbose_name="Tartib")

    class Meta:
        db_table = 'admission_subjects'
        verbose_name = "Imtihon fani"
        verbose_name_plural = "Imtihon fanlari"
        ordering = ['sort_order']
        indexes = [
            models.Index(fields=['subject_type']),
            models.Index(fields=['sort_order']),
        ]

    def __str__(self):
        return self.subject_name_uz or self.subject_name_ru or self.subject_name_en or f"Subject #{self.pk}"


class AdmissionDocument(models.Model):
    # Tarjima maydonlari
    document_name_uz = models.CharField(max_length=300, blank=True, verbose_name="Hujjat nomi (UZ)")
    document_name_uz_cyrl = models.CharField(max_length=300, blank=True, verbose_name="Hujjat nomi (UZ Kirill)")
    document_name_ru = models.CharField(max_length=300, blank=True, verbose_name="Hujjat nomi (RU)")
    document_name_en = models.CharField(max_length=300, blank=True, verbose_name="Hujjat nomi (EN)")

    note_uz = models.CharField(max_length=500, null=True, blank=True, verbose_name="Izoh (UZ)")
    note_uz_cyrl = models.CharField(max_length=500, null=True, blank=True, verbose_name="Izoh (UZ Kirill)")
    note_ru = models.CharField(max_length=500, null=True, blank=True, verbose_name="Izoh (RU)")
    note_en = models.CharField(max_length=500, null=True, blank=True, verbose_name="Izoh (EN)")

    document_file = models.FileField(
        upload_to='admission_documents/', null=True, blank=True, verbose_name="Hujjat fayli"
    )
    is_required = models.BooleanField(default=True, verbose_name="Majburiy")
    sort_order = models.IntegerField(default=0, verbose_name="Tartib")

    class Meta:
        db_table = 'admission_documents'
        verbose_name = "Talab qilinadigan hujjat"
        verbose_name_plural = "Talab qilinadigan hujjatlar"
        ordering = ['sort_order']
        indexes = [
            models.Index(fields=['is_required']),
            models.Index(fields=['sort_order']),
        ]

    def __str__(self):
        return self.document_name_uz or self.document_name_ru or self.document_name_en or f"Document #{self.pk}"


class FAQ(models.Model):
    class Category(models.TextChoices):
        ADMISSION = 'admission', 'Qabul'
        GENERAL = 'general', 'Umumiy'
        EDUCATION = 'education', "Ta'lim"
        PAYMENT = 'payment', "To'lov"

    # Tarjima maydonlari
    question_uz = models.TextField(blank=True, verbose_name="Savol (UZ)")
    question_uz_cyrl = models.TextField(blank=True, verbose_name="Savol (UZ Kirill)")
    question_ru = models.TextField(blank=True, verbose_name="Savol (RU)")
    question_en = models.TextField(blank=True, verbose_name="Savol (EN)")

    answer_uz = models.TextField(blank=True, verbose_name="Javob (UZ)")
    answer_uz_cyrl = models.TextField(blank=True, verbose_name="Javob (UZ Kirill)")
    answer_ru = models.TextField(blank=True, verbose_name="Javob (RU)")
    answer_en = models.TextField(blank=True, verbose_name="Javob (EN)")

    category = models.CharField(
        max_length=20, choices=Category.choices,
        default=Category.GENERAL, verbose_name="Kategoriya"
    )
    is_featured = models.BooleanField(default=False, verbose_name="Bosh sahifaga chiqarish")
    sort_order = models.IntegerField(default=0, verbose_name="Tartib")
    is_active = models.BooleanField(default=True, verbose_name="Faol")

    class Meta:
        db_table = 'faqs'
        verbose_name = "FAQ"
        verbose_name_plural = "FAQ lar"
        ordering = ['sort_order']
        indexes = [
            models.Index(fields=['category', 'is_active']),
            models.Index(fields=['is_featured', 'is_active']),
            models.Index(fields=['sort_order']),
        ]

    def __str__(self):
        q = self.question_uz or self.question_ru or self.question_en or ''
        return q[:100]
