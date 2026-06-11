from django.db import models
from django.utils import timezone


class ContactMessage(models.Model):
    """Sayt tashrif buyuruvchilaridan kelgan xabarlar"""
    
    class Status(models.TextChoices):
        NEW = 'new', 'Yangi'
        READ = 'read', "O'qilgan"
        REPLIED = 'replied', 'Javob berilgan'
        ARCHIVED = 'archived', 'Arxivlangan'
    
    class Subject(models.TextChoices):
        ADMISSION = 'admission', 'Qabul'
        GENERAL = 'general', 'Umumiy savol'
        COMPLAINT = 'complaint', 'Shikoyat'
        SUGGESTION = 'suggestion', 'Taklif'
        OTHER = 'other', 'Boshqa'
    
    # Yuboruvchi ma'lumotlari
    full_name = models.CharField(max_length=200, verbose_name="Ism-familiya")
    email = models.EmailField(verbose_name="Email manzil")
    phone = models.CharField(max_length=20, verbose_name="Telefon raqam")
    subject = models.CharField(
        max_length=20, 
        choices=Subject.choices, 
        default=Subject.GENERAL,
        verbose_name="Mavzu"
    )
    
    # Xabar matni
    message = models.TextField(verbose_name="Xabar")
    
    # Status va javob
    status = models.CharField(
        max_length=20, 
        choices=Status.choices, 
        default=Status.NEW,
        verbose_name="Holat"
    )
    reply = models.TextField(blank=True, null=True, verbose_name="Javob")
    replied_by = models.ForeignKey(
        'accounts.User', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='contact_replies',
        verbose_name="Javob bergan"
    )
    replied_at = models.DateTimeField(null=True, blank=True, verbose_name="Javob berilgan vaqt")
    
    # Qo'shimcha ma'lumotlar
    ip_address = models.GenericIPAddressField(null=True, blank=True, verbose_name="IP manzil")
    user_agent = models.TextField(blank=True, null=True, verbose_name="Brauzer ma'lumoti")
    
    # Vaqt belgilari
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Yaratilgan")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Yangilangan")
    read_at = models.DateTimeField(null=True, blank=True, verbose_name="O'qilgan vaqt")
    
    class Meta:
        db_table = 'contact_messages'
        verbose_name = "Xabar"
        verbose_name_plural = "Xabarlar"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['email']),
        ]
    
    def __str__(self):
        return f"{self.full_name} - {self.subject} ({self.created_at.strftime('%d.%m.%Y')})"
    
    def mark_as_read(self):
        """Xabarni o'qilgan deb belgilash"""
        if self.status == self.Status.NEW:
            self.status = self.Status.READ
            self.read_at = timezone.now()
            self.save(update_fields=['status', 'read_at', 'updated_at'])
    
    def mark_as_replied(self, reply_text, user):
        """Javob berilgan deb belgilash"""
        self.reply = reply_text
        self.replied_by = user
        self.replied_at = timezone.now()
        self.status = self.Status.REPLIED
        self.save(update_fields=['reply', 'replied_by', 'replied_at', 'status', 'updated_at'])
    
    @property
    def is_new(self):
        return self.status == self.Status.NEW
    
    @property
    def response_time(self):
        """Javob berish vaqti (soatlarda)"""
        if self.replied_at:
            delta = self.replied_at - self.created_at
            return round(delta.total_seconds() / 3600, 1)
        return None
