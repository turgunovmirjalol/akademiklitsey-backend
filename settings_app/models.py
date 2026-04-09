from django.db import models


class SiteSettings(models.Model):
    """
    Sayt sozlamalari — faqat bitta yozuv bo'lishi kerak (Singleton).
    short_name, full_name, address — ko'p tilli.
    """

    # Tarjima maydonlari
    short_name_uz = models.CharField(max_length=100, blank=True, verbose_name="Qisqa nomi (UZ)")
    short_name_uz_cyrl = models.CharField(max_length=100, blank=True, verbose_name="Qisqa nomi (UZ Kirill)")
    short_name_ru = models.CharField(max_length=100, blank=True, verbose_name="Qisqa nomi (RU)")
    short_name_en = models.CharField(max_length=100, blank=True, verbose_name="Qisqa nomi (EN)")

    full_name_uz = models.CharField(max_length=300, blank=True, verbose_name="To'liq nomi (UZ)")
    full_name_uz_cyrl = models.CharField(max_length=300, blank=True, verbose_name="To'liq nomi (UZ Kirill)")
    full_name_ru = models.CharField(max_length=300, blank=True, verbose_name="To'liq nomi (RU)")
    full_name_en = models.CharField(max_length=300, blank=True, verbose_name="To'liq nomi (EN)")

    address_uz = models.CharField(max_length=300, blank=True, verbose_name="Manzil (UZ)")
    address_uz_cyrl = models.CharField(max_length=300, blank=True, verbose_name="Manzil (UZ Kirill)")
    address_ru = models.CharField(max_length=300, blank=True, verbose_name="Manzil (RU)")
    address_en = models.CharField(max_length=300, blank=True, verbose_name="Manzil (EN)")

    # Umumiy maydonlar (tarjima talab qilmaydi)
    established_year = models.PositiveIntegerField(
        default=2000, verbose_name="Tashkil etilgan yili"
    )
    phone = models.CharField(max_length=50, blank=True, verbose_name="Telefon")
    email = models.EmailField(blank=True, verbose_name="Email")
    website = models.URLField(blank=True, verbose_name="Veb-sayt")
    logo = models.ImageField(
        upload_to='settings/', blank=True, null=True, verbose_name="Logo"
    )

    # Ijtimoiy tarmoqlar
    telegram = models.URLField(blank=True, null=True, verbose_name="Telegram")
    instagram = models.URLField(blank=True, null=True, verbose_name="Instagram")
    facebook = models.URLField(blank=True, null=True, verbose_name="Facebook")
    youtube = models.URLField(blank=True, null=True, verbose_name="YouTube")

    class Meta:
        db_table = 'site_settings'
        verbose_name = "Sayt sozlamalari"
        verbose_name_plural = "Sayt sozlamalari"

    def __str__(self):
        return self.short_name_uz or self.short_name_ru or "Sayt sozlamalari"

    def save(self, *args, **kwargs):
        """Singleton — faqat bitta yozuv bo'lishi uchun."""
        if not self.pk and SiteSettings.objects.exists():
            self.pk = SiteSettings.objects.first().pk
        super().save(*args, **kwargs)

    @classmethod
    def get_instance(cls):
        """Yagona instance ni qaytaradi yoki None."""
        return cls.objects.first()
