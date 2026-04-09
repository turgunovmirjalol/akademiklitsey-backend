from django.db import models


class Statistic(models.Model):
    """
    Bosh sahifa statistikalari.
    key   — texnik identifikator (o'zgarmas)
    value — raqamli qiymat
    label — ko'p tilli yorliq (frontendda ko'rsatiladi)
    icon  — CSS/font-awesome icon classi
    """
    key = models.CharField(
        max_length=50, unique=True,
        verbose_name="Kalit (texnik)"
    )
    value = models.PositiveIntegerField(
        default=0,
        verbose_name="Qiymat"
    )

    # Tarjima maydonlari
    label_uz = models.CharField(
        max_length=100, blank=True,
        verbose_name="Yorliq (UZ)"
    )
    label_uz_cyrl = models.CharField(
        max_length=100, blank=True,
        verbose_name="Yorliq (UZ Kirill)"
    )
    label_ru = models.CharField(
        max_length=100, blank=True,
        verbose_name="Yorliq (RU)"
    )
    label_en = models.CharField(
        max_length=100, blank=True,
        verbose_name="Yorliq (EN)"
    )

    icon = models.CharField(
        max_length=100, blank=True, null=True,
        verbose_name="Icon classi (masalan: fa-users)"
    )
    sort_order = models.PositiveIntegerField(
        default=1,
        verbose_name="Tartib"
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'statistics'
        verbose_name = "Statistika"
        verbose_name_plural = "Statistikalar"
        ordering = ['sort_order']

    def __str__(self):
        label = self.label_uz or self.label_ru or self.label_en or self.key
        return f"{label}: {self.value}"

    def get_label(self, lang='uz'):
        """Berilgan tildagi yorliqni qaytaradi, yo'q bo'lsa uz ga fallback."""
        lang_key = lang.replace('-', '_')
        return getattr(self, f'label_{lang_key}', '') or self.label_uz or self.label_ru or self.key
