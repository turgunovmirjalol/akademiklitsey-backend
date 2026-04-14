from rest_framework import serializers
from .models import GalleryAlbum, GalleryPhoto, UsefulLink

LANGS = ['uz', 'uz_cyrl', 'ru', 'en']


def build_translations(obj, fields):
    """Barcha tillar uchun tarjimalarni qaytaradi. Bosh bolsa ham bosh string bilan."""
    result = {}
    for lang in LANGS:
        data = {}
        for field in fields:
            val = getattr(obj, f"{field}_{lang}", None)
            data[field] = val if val is not None else ''
        result[lang] = data
    return result


def apply_lang_filter(data, lang):
    """?lang= berilganda faqat o'sha tilni, yo'q bolsa uz fallback."""
    if not lang or lang not in LANGS:
        return data
    def _filter(item):
        if isinstance(item, dict) and 'translations' in item:
            t = item.get('translations') or {}
            chosen = t.get(lang, {})
            if not any(chosen.values()):
                chosen = t.get('uz', {})
            item = dict(item)
            item['translations'] = {lang: chosen}
        return item
    if isinstance(data, list):
        return [_filter(i) for i in data]
    return _filter(data)


# ─────────────────────────────────────────────────────────────────────────────
# GalleryPhoto
# ─────────────────────────────────────────────────────────────────────────────

class GalleryPhotoSerializer(serializers.Serializer):
    """Read serializer — albom ichidagi rasmlar."""
    id = serializers.IntegerField(read_only=True)
    image = serializers.SerializerMethodField()
    thumbnail = serializers.SerializerMethodField()
    caption = serializers.CharField(allow_null=True, allow_blank=True)
    sort_order = serializers.IntegerField()
    created_at = serializers.DateTimeField(read_only=True)

    def get_image(self, obj):
        if obj.image:
            request = self.context.get('request')
            return request.build_absolute_uri(obj.image.url) if request else obj.image.url
        return None

    def get_thumbnail(self, obj):
        if obj.thumbnail:
            request = self.context.get('request')
            return request.build_absolute_uri(obj.thumbnail.url) if request else obj.thumbnail.url
        return None


class GalleryPhotoUploadSerializer(serializers.Serializer):
    """
    Albomga rasm yuklash uchun.
    image — majburiy, thumbnail — ixtiyoriy.
    multipart/form-data orqali yuboriladi.
    """
    image = serializers.ImageField(
        help_text="Asosiy rasm (majburiy). JPEG, PNG, WEBP."
    )
    thumbnail = serializers.ImageField(
        required=False, allow_null=True,
        help_text="Kichik preview rasm (ixtiyoriy). Yo'q bo'lsa image ishlatiladi."
    )
    caption = serializers.CharField(
        max_length=500, required=False, allow_blank=True, allow_null=True,
        help_text="Rasm izohi (ixtiyoriy)"
    )
    sort_order = serializers.IntegerField(
        default=0,
        help_text="Tartib raqami (ixtiyoriy, avtomatik belgilanadi)"
    )

    def create(self, validated_data):
        return GalleryPhoto.objects.create(**validated_data)


class GalleryPhotoBulkUploadSerializer(serializers.Serializer):
    """
    Bir vaqtda bir nechta rasm yuklash.
    images[] — bir nechta fayl.
    """
    images = serializers.ListField(
        child=serializers.ImageField(),
        help_text="Bir nechta rasm fayllari (images[])"
    )
    caption = serializers.CharField(
        max_length=500, required=False, allow_blank=True, allow_null=True,
        help_text="Barcha rasmlarga umumiy izoh (ixtiyoriy)"
    )


# ─────────────────────────────────────────────────────────────────────────────
# GalleryAlbum
# ─────────────────────────────────────────────────────────────────────────────

class GalleryAlbumSerializer(serializers.Serializer):
    """Read serializer — ro'yxat uchun (rasmlar yo'q)."""
    id = serializers.IntegerField(read_only=True)
    slug = serializers.SlugField(read_only=True)
    translations = serializers.SerializerMethodField()
    cover_image = serializers.SerializerMethodField()
    event_date = serializers.DateField(allow_null=True)
    photos_count = serializers.IntegerField(read_only=True)
    is_active = serializers.BooleanField()
    sort_order = serializers.IntegerField()
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)

    def get_translations(self, obj):
        return build_translations(obj, ['title', 'description'])

    def get_cover_image(self, obj):
        if obj.cover_image:
            request = self.context.get('request')
            return request.build_absolute_uri(obj.cover_image.url) if request else obj.cover_image.url
        return None


class GalleryAlbumDetailSerializer(GalleryAlbumSerializer):
    """Read serializer — detail uchun (rasmlar bilan)."""
    photos = serializers.SerializerMethodField()

    def get_photos(self, obj):
        photos = obj.photos.all().order_by('sort_order', 'created_at')
        return GalleryPhotoSerializer(photos, many=True, context=self.context).data


class GalleryAlbumWriteSerializer(serializers.Serializer):
    """
    Write serializer. Har bir til maydoni alohida flat field.
    cover_image — multipart/form-data orqali yuboriladi.
    Kamida bitta tilda title_* to'ldirilishi shart.
    """
    title_uz = serializers.CharField(
        max_length=300, required=False, allow_blank=True,
        help_text="Album nomi (O'zbek lotin)"
    )
    title_uz_cyrl = serializers.CharField(
        max_length=300, required=False, allow_blank=True,
        help_text="Album nomi (O'zbek kirill)"
    )
    title_ru = serializers.CharField(
        max_length=300, required=False, allow_blank=True,
        help_text="Album nomi (Rus)"
    )
    title_en = serializers.CharField(
        max_length=300, required=False, allow_blank=True,
        help_text="Album nomi (Ingliz)"
    )
    description_uz = serializers.CharField(
        required=False, allow_blank=True, allow_null=True,
        help_text="Tavsif (O'zbek lotin)"
    )
    description_uz_cyrl = serializers.CharField(
        required=False, allow_blank=True, allow_null=True,
        help_text="Tavsif (O'zbek kirill)"
    )
    description_ru = serializers.CharField(
        required=False, allow_blank=True, allow_null=True,
        help_text="Tavsif (Rus)"
    )
    description_en = serializers.CharField(
        required=False, allow_blank=True, allow_null=True,
        help_text="Tavsif (Ingliz)"
    )
    cover_image = serializers.ImageField(
        required=False, allow_null=True,
        help_text="Muqova rasmi (multipart/form-data)"
    )
    event_date = serializers.DateField(
        required=False, allow_null=True,
        help_text="Tadbir sanasi (YYYY-MM-DD)"
    )
    is_active = serializers.BooleanField(default=True)
    sort_order = serializers.IntegerField(default=0)

    def validate(self, data):
        if self.partial:
            instance = self.instance
            titles = [
                data.get(f'title_{l}') or (getattr(instance, f'title_{l}', '') if instance else '')
                for l in ['uz', 'ru', 'en', 'uz_cyrl']
            ]
        else:
            titles = [data.get(f'title_{l}', '') for l in ['uz', 'ru', 'en', 'uz_cyrl']]
        if not any(titles):
            raise serializers.ValidationError(
                "Kamida bitta tilda album nomi kiritilishi shart (title_uz, title_ru yoki title_en)."
            )
        return data

    def create(self, validated_data):
        return GalleryAlbum.objects.create(**validated_data)

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


# ─────────────────────────────────────────────────────────────────────────────
# UsefulLink
# ─────────────────────────────────────────────────────────────────────────────

class UsefulLinkSerializer(serializers.Serializer):
    """Read serializer."""
    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField()
    url = serializers.URLField()
    logo = serializers.SerializerMethodField()
    description = serializers.CharField(allow_null=True, allow_blank=True)
    sort_order = serializers.IntegerField()
    is_active = serializers.BooleanField()
    created_at = serializers.DateTimeField(read_only=True)

    def get_logo(self, obj):
        if obj.logo:
            request = self.context.get('request')
            return request.build_absolute_uri(obj.logo.url) if request else obj.logo.url
        return None


class UsefulLinkWriteSerializer(serializers.Serializer):
    """
    Write serializer. logo — multipart/form-data orqali yuboriladi.
    """
    name = serializers.CharField(
        max_length=200,
        help_text="Havola nomi"
    )
    url = serializers.URLField(
        max_length=500,
        help_text="To'liq URL manzil (https://...)"
    )
    logo = serializers.ImageField(
        required=False, allow_null=True,
        help_text="Logo rasmi (ixtiyoriy, multipart/form-data)"
    )
    description = serializers.CharField(
        max_length=300, required=False, allow_blank=True, allow_null=True,
        help_text="Qisqa tavsif (ixtiyoriy)"
    )
    sort_order = serializers.IntegerField(default=0)
    is_active = serializers.BooleanField(default=True)

    def create(self, validated_data):
        return UsefulLink.objects.create(**validated_data)

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance
