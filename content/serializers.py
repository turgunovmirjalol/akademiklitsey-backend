from rest_framework import serializers
from .models import News, Announcement

LANGS = ['uz', 'uz_cyrl', 'ru', 'en']
NEWS_FIELDS = ['title', 'short_description', 'content']
ANN_FIELDS = ['title', 'short_description', 'content']


def build_translations(obj, fields):
    """Model instance dan barcha tillardagi tarjimalarni dict sifatida qaytaradi."""
    result = {}
    for lang in LANGS:
        data = {}
        for field in fields:
            val = getattr(obj, f"{field}_{lang}", None) or ''
            data[field] = val
        if any(data.values()):
            result[lang] = data
    return result


def apply_lang_filter(data, lang):
    """Response data dan faqat berilgan tildagi translations ni qaytaradi."""
    if not lang or lang not in LANGS:
        return data
    def _filter(item):
        if isinstance(item, dict) and 'translations' in item:
            t = item.get('translations') or {}
            item = dict(item)
            item['translations'] = {lang: t.get(lang, {})} if t else {}
        return item
    if isinstance(data, list):
        return [_filter(i) for i in data]
    return _filter(data)


# ─────────────────────────────────────────────────────────────────────────────
# News
# ─────────────────────────────────────────────────────────────────────────────

class NewsSerializer(serializers.Serializer):
    """Read serializer — ro'yxat va detail uchun."""
    id = serializers.IntegerField(read_only=True)
    slug = serializers.SlugField(read_only=True)
    translations = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()
    views_count = serializers.IntegerField(read_only=True)
    status = serializers.CharField()
    status_display = serializers.SerializerMethodField()
    is_featured = serializers.BooleanField()
    published_at = serializers.DateTimeField(allow_null=True)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)
    created_by = serializers.StringRelatedField(read_only=True)

    def get_translations(self, obj):
        return build_translations(obj, NEWS_FIELDS)

    def get_image(self, obj):
        if obj.image:
            request = self.context.get('request')
            return request.build_absolute_uri(obj.image.url) if request else obj.image.url
        return None

    def get_status_display(self, obj):
        return obj.get_status_display()


class NewsWriteSerializer(serializers.Serializer):
    """
    Write serializer. Har bir til maydoni alohida flat field.
    Rasm yuklash uchun multipart/form-data ishlatiladi.
    Kamida bitta tilda title_* to'ldirilishi shart.
    """
    # Tarjima maydonlari
    title_uz = serializers.CharField(
        max_length=300, required=False, allow_blank=True,
        help_text="Sarlavha (O'zbek lotin)"
    )
    title_uz_cyrl = serializers.CharField(
        max_length=300, required=False, allow_blank=True,
        help_text="Sarlavha (O'zbek kirill)"
    )
    title_ru = serializers.CharField(
        max_length=300, required=False, allow_blank=True,
        help_text="Sarlavha (Rus)"
    )
    title_en = serializers.CharField(
        max_length=300, required=False, allow_blank=True,
        help_text="Sarlavha (Ingliz)"
    )
    short_description_uz = serializers.CharField(
        required=False, allow_blank=True,
        help_text="Qisqa tavsif (O'zbek lotin)"
    )
    short_description_uz_cyrl = serializers.CharField(
        required=False, allow_blank=True,
        help_text="Qisqa tavsif (O'zbek kirill)"
    )
    short_description_ru = serializers.CharField(
        required=False, allow_blank=True,
        help_text="Qisqa tavsif (Rus)"
    )
    short_description_en = serializers.CharField(
        required=False, allow_blank=True,
        help_text="Qisqa tavsif (Ingliz)"
    )
    content_uz = serializers.CharField(
        required=False, allow_blank=True,
        help_text="To'liq matn (O'zbek lotin)"
    )
    content_uz_cyrl = serializers.CharField(
        required=False, allow_blank=True,
        help_text="To'liq matn (O'zbek kirill)"
    )
    content_ru = serializers.CharField(
        required=False, allow_blank=True,
        help_text="To'liq matn (Rus)"
    )
    content_en = serializers.CharField(
        required=False, allow_blank=True,
        help_text="To'liq matn (Ingliz)"
    )
    # Umumiy maydonlar
    image = serializers.ImageField(
        required=False, allow_null=True,
        help_text="Asosiy rasm (multipart/form-data)"
    )
    status = serializers.ChoiceField(
        choices=News.Status.choices,
        default=News.Status.DRAFT,
        help_text="draft | published | archived"
    )
    is_featured = serializers.BooleanField(
        default=False,
        help_text="Bosh sahifaga chiqarish"
    )
    published_at = serializers.DateTimeField(
        required=False, allow_null=True,
        help_text="Nashr sanasi (bo'sh qoldirilsa status=published da avtomatik to'ldiriladi)"
    )

    def validate(self, data):
        titles = [
            data.get('title_uz', ''),
            data.get('title_ru', ''),
            data.get('title_en', ''),
            data.get('title_uz_cyrl', ''),
        ]
        if not any(titles):
            raise serializers.ValidationError(
                "Kamida bitta tilda sarlavha kiritilishi shart (title_uz, title_ru yoki title_en)."
            )
        return data

    def create(self, validated_data):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            validated_data['created_by'] = request.user
        return News.objects.create(**validated_data)

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


# ─────────────────────────────────────────────────────────────────────────────
# Announcement
# ─────────────────────────────────────────────────────────────────────────────

class AnnouncementSerializer(serializers.Serializer):
    """Read serializer — ro'yxat va detail uchun."""
    id = serializers.IntegerField(read_only=True)
    slug = serializers.SlugField(read_only=True)
    translations = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()
    views_count = serializers.IntegerField(read_only=True)
    status = serializers.CharField()
    status_display = serializers.SerializerMethodField()
    is_important = serializers.BooleanField()
    is_expired = serializers.BooleanField(read_only=True)
    expires_at = serializers.DateTimeField(allow_null=True)
    published_at = serializers.DateTimeField(allow_null=True)
    created_at = serializers.DateTimeField(read_only=True)
    created_by = serializers.StringRelatedField(read_only=True)

    def get_translations(self, obj):
        return build_translations(obj, ANN_FIELDS)

    def get_image(self, obj):
        if obj.image:
            request = self.context.get('request')
            return request.build_absolute_uri(obj.image.url) if request else obj.image.url
        return None

    def get_status_display(self, obj):
        return obj.get_status_display()


class AnnouncementWriteSerializer(serializers.Serializer):
    """
    Write serializer. Har bir til maydoni alohida flat field.
    Kamida bitta tilda title_* to'ldirilishi shart.
    """
    # Tarjima maydonlari
    title_uz = serializers.CharField(
        max_length=300, required=False, allow_blank=True,
        help_text="Sarlavha (O'zbek lotin)"
    )
    title_uz_cyrl = serializers.CharField(
        max_length=300, required=False, allow_blank=True,
        help_text="Sarlavha (O'zbek kirill)"
    )
    title_ru = serializers.CharField(
        max_length=300, required=False, allow_blank=True,
        help_text="Sarlavha (Rus)"
    )
    title_en = serializers.CharField(
        max_length=300, required=False, allow_blank=True,
        help_text="Sarlavha (Ingliz)"
    )
    short_description_uz = serializers.CharField(
        required=False, allow_blank=True,
        help_text="Qisqa tavsif (O'zbek lotin)"
    )
    short_description_uz_cyrl = serializers.CharField(
        required=False, allow_blank=True,
        help_text="Qisqa tavsif (O'zbek kirill)"
    )
    short_description_ru = serializers.CharField(
        required=False, allow_blank=True,
        help_text="Qisqa tavsif (Rus)"
    )
    short_description_en = serializers.CharField(
        required=False, allow_blank=True,
        help_text="Qisqa tavsif (Ingliz)"
    )
    content_uz = serializers.CharField(
        required=False, allow_blank=True,
        help_text="To'liq matn (O'zbek lotin)"
    )
    content_uz_cyrl = serializers.CharField(
        required=False, allow_blank=True,
        help_text="To'liq matn (O'zbek kirill)"
    )
    content_ru = serializers.CharField(
        required=False, allow_blank=True,
        help_text="To'liq matn (Rus)"
    )
    content_en = serializers.CharField(
        required=False, allow_blank=True,
        help_text="To'liq matn (Ingliz)"
    )
    # Umumiy maydonlar
    image = serializers.ImageField(
        required=False, allow_null=True,
        help_text="Asosiy rasm (multipart/form-data)"
    )
    status = serializers.ChoiceField(
        choices=Announcement.Status.choices,
        default=Announcement.Status.DRAFT,
        help_text="draft | published | archived"
    )
    is_important = serializers.BooleanField(
        default=False,
        help_text="Muhim e'lon sifatida belgilash"
    )
    expires_at = serializers.DateTimeField(
        required=False, allow_null=True,
        help_text="Muddati tugash sanasi (ixtiyoriy)"
    )
    published_at = serializers.DateTimeField(
        required=False, allow_null=True,
        help_text="Nashr sanasi (bo'sh qoldirilsa status=published da avtomatik)"
    )

    def validate(self, data):
        titles = [
            data.get('title_uz', ''),
            data.get('title_ru', ''),
            data.get('title_en', ''),
            data.get('title_uz_cyrl', ''),
        ]
        if not any(titles):
            raise serializers.ValidationError(
                "Kamida bitta tilda sarlavha kiritilishi shart (title_uz, title_ru yoki title_en)."
            )
        return data

    def create(self, validated_data):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            validated_data['created_by'] = request.user
        return Announcement.objects.create(**validated_data)

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


# Backward compat aliases
NewsListSerializer = NewsSerializer
NewsDetailSerializer = NewsSerializer
AnnouncementListSerializer = AnnouncementSerializer
AnnouncementDetailSerializer = AnnouncementSerializer
