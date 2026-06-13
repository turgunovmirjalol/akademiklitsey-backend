from django.db import models


class Slider(models.Model):
    """
    Bosh sahifa slider — rasm, title va description ko'p tilli (uz, ru).
    """
    image = models.ImageField(upload_to='slider/', verbose_name="Rasm")

    title_uz      = models.CharField(max_length=200, blank=True, verbose_name="Sarlavha (UZ)")
    title_ru      = models.CharField(max_length=200, blank=True, verbose_name="Sarlavha (RU)")

    description_uz      = models.TextField(blank=True, verbose_name="Tavsif (UZ)")
    description_ru      = models.TextField(blank=True, verbose_name="Tavsif (RU)")

    sort_order = models.PositiveIntegerField(default=1, verbose_name="Tartib raqami")
    is_active  = models.BooleanField(default=True, verbose_name="Faol")

    class Meta:
        db_table = 'slider'
        verbose_name = "Slider"
        verbose_name_plural = "Slayderlar"
        ordering = ['sort_order']

    def __str__(self):
        return self.title_uz or self.title_ru or f"Slider #{self.pk}"


class SiteSettings(models.Model):
    """
    Sayt sozlamalari — faqat bitta yozuv bo'lishi kerak (Singleton).
    short_name, full_name, address — ko'p tilli.
    """

    # Tarjima maydonlari
    short_name_uz = models.CharField(max_length=100, blank=True, verbose_name="Qisqa nomi (UZ)")
    short_name_ru = models.CharField(max_length=100, blank=True, verbose_name="Qisqa nomi (RU)")

    full_name_uz = models.CharField(max_length=300, blank=True, verbose_name="To'liq nomi (UZ)")
    full_name_ru = models.CharField(max_length=300, blank=True, verbose_name="To'liq nomi (RU)")

    address_uz = models.CharField(max_length=300, blank=True, verbose_name="Manzil (UZ)")
    address_ru = models.CharField(max_length=300, blank=True, verbose_name="Manzil (RU)")

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
