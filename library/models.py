from django.db import models


class LibraryStats(models.Model):
    """
    Kutubxona statistikasi — bitta yozuv (singleton).
    Rasmda: 5000+ kitoblar, 500+ elektron resurslar, 50+ jurnallar, 100+ o'quv qo'llanmalari
    """
    books_count = models.PositiveIntegerField(default=0, verbose_name="Kitoblar soni")
    books_suffix = models.CharField(max_length=10, default='+', blank=True, verbose_name="Kitoblar suffiks")

    electronic_resources_count = models.PositiveIntegerField(default=0, verbose_name="Elektron resurslar soni")
    electronic_resources_suffix = models.CharField(max_length=10, default='+', blank=True, verbose_name="Elektron resurslar suffiks")

    journals_count = models.PositiveIntegerField(default=0, verbose_name="Jurnallar soni")
    journals_suffix = models.CharField(max_length=10, default='+', blank=True, verbose_name="Jurnallar suffiks")

    manuals_count = models.PositiveIntegerField(default=0, verbose_name="O'quv qo'llanmalari soni")
    manuals_suffix = models.CharField(max_length=10, default='+', blank=True, verbose_name="O'quv qo'llanmalari suffiks")

    updated_at = models.DateTimeField(auto_now=True, verbose_name="Yangilangan vaqt")

    class Meta:
        db_table = 'library_stats'
        verbose_name = "Kutubxona statistikasi"
        verbose_name_plural = "Kutubxona statistikasi"

    def __str__(self):
        return "Kutubxona statistikasi"

    def save(self, *args, **kwargs):
        # Singleton: faqat bitta yozuv bo'lishi kerak
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def get_instance(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj


class LibraryResource(models.Model):
    """
    Kutubxona resursi — kitob, jurnal, o'quv qo'llanma va h.k.
    """

    class Category(models.TextChoices):
        DARSLIK = 'darslik', 'Darsliklar'
        QOLLANMA = 'qollanma', "Go'llanmalar"
        JURNAL = 'jurnal', 'Jurnallar'
        AMALIY = 'amaliy', "Amaliy qo'llanmalar"
        ELEKTRON = 'elektron', 'Elektron resurslar'
        BOSHQA = 'boshqa', 'Boshqa'

    class FileType(models.TextChoices):
        PDF = 'pdf', 'PDF'
        DOCX = 'docx', 'DOCX'
        XLSX = 'xlsx', 'XLSX'
        PPTX = 'pptx', 'PPTX'
        OTHER = 'other', 'Boshqa'

    # Tarjima maydonlari — nom
    title_uz = models.CharField(max_length=300, blank=True, verbose_name="Nomi (UZ)")
    title_ru = models.CharField(max_length=300, blank=True, verbose_name="Nomi (RU)")

    # Tarjima maydonlari — tavsif
    description_uz = models.TextField(blank=True, verbose_name="Tavsif (UZ)")
    description_ru = models.TextField(blank=True, verbose_name="Tavsif (RU)")

    # Muallif
    author = models.CharField(max_length=300, blank=True, verbose_name="Muallif")

    category = models.CharField(
        max_length=20,
        choices=Category.choices,
        default=Category.DARSLIK,
        verbose_name="Kategoriya",
    )
    file_type = models.CharField(
        max_length=10,
        choices=FileType.choices,
        default=FileType.PDF,
        verbose_name="Fayl turi",
    )
    file = models.FileField(
        upload_to='library/resources/',
        null=True, blank=True,
        verbose_name="Fayl",
    )
    cover_image = models.ImageField(
        upload_to='library/covers/',
        null=True, blank=True,
        verbose_name="Muqova rasmi",
    )
    is_featured = models.BooleanField(default=False, verbose_name="Mashhur (bosh sahifaga)")
    is_active = models.BooleanField(default=True, verbose_name="Faol")
    sort_order = models.IntegerField(default=0, verbose_name="Tartib")
    download_count = models.PositiveIntegerField(default=0, verbose_name="Yuklab olishlar soni")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Yaratilgan vaqt")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Yangilangan vaqt")

    class Meta:
        db_table = 'library_resources'
        verbose_name = "Kutubxona resursi"
        verbose_name_plural = "Kutubxona resurslari"
        ordering = ['sort_order', '-created_at']
        indexes = [
            models.Index(fields=['category', 'is_active'], name='lib_res_cat_active_idx'),
            models.Index(fields=['is_featured', 'is_active'], name='lib_res_featured_idx'),
            models.Index(fields=['sort_order'], name='lib_res_sort_idx'),
        ]

    def __str__(self):
        return self.title_uz or self.title_ru or f"Resurs #{self.pk}"
