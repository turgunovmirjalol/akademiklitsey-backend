from rest_framework import serializers
from .models import SiteSettings

LANGS = ['uz', 'uz_cyrl', 'ru', 'en']
TRANS_FIELDS = ['short_name', 'full_name', 'address']


def build_translations(obj, fields):
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
    if not lang or lang not in LANGS:
        return data
    if isinstance(data, dict) and 'translations' in data:
        t = data.get('translations') or {}
        data = dict(data)
        data['translations'] = {lang: t.get(lang, {})} if t else {}
    return data


class SiteSettingsSerializer(serializers.Serializer):
    """
    Read serializer.
    translations — {"uz": {"short_name": "...", "full_name": "...", "address": "..."}, "ru": {...}}
    """
    id = serializers.IntegerField(read_only=True)
    translations = serializers.SerializerMethodField()
    established_year = serializers.IntegerField()
    phone = serializers.CharField(allow_blank=True)
    email = serializers.EmailField(allow_blank=True)
    website = serializers.URLField(allow_blank=True)
    logo = serializers.SerializerMethodField()
    # Ijtimoiy tarmoqlar
    telegram = serializers.URLField(allow_null=True, allow_blank=True)
    instagram = serializers.URLField(allow_null=True, allow_blank=True)
    facebook = serializers.URLField(allow_null=True, allow_blank=True)
    youtube = serializers.URLField(allow_null=True, allow_blank=True)

    def get_translations(self, obj):
        return build_translations(obj, TRANS_FIELDS)

    def get_logo(self, obj):
        if obj.logo:
            request = self.context.get('request')
            return request.build_absolute_uri(obj.logo.url) if request else obj.logo.url
        return None


class SiteSettingsWriteSerializer(serializers.Serializer):
    """
    Write serializer. Har bir til maydoni alohida flat field.
    Logo yuklash uchun multipart/form-data ishlatiladi.
    Kamida bitta tilda short_name_* va full_name_* to'ldirilishi shart.
    """
    # Tarjima maydonlari
    short_name_uz = serializers.CharField(
        max_length=100, required=False, allow_blank=True,
        help_text="Qisqa nomi (O'zbek lotin). Masalan: Akademik Litsey"
    )
    short_name_uz_cyrl = serializers.CharField(
        max_length=100, required=False, allow_blank=True,
        help_text="Qisqa nomi (O'zbek kirill)"
    )
    short_name_ru = serializers.CharField(
        max_length=100, required=False, allow_blank=True,
        help_text="Qisqa nomi (Rus)"
    )
    short_name_en = serializers.CharField(
        max_length=100, required=False, allow_blank=True,
        help_text="Qisqa nomi (Ingliz)"
    )
    full_name_uz = serializers.CharField(
        max_length=300, required=False, allow_blank=True,
        help_text="To'liq nomi (O'zbek lotin)"
    )
    full_name_uz_cyrl = serializers.CharField(
        max_length=300, required=False, allow_blank=True,
        help_text="To'liq nomi (O'zbek kirill)"
    )
    full_name_ru = serializers.CharField(
        max_length=300, required=False, allow_blank=True,
        help_text="To'liq nomi (Rus)"
    )
    full_name_en = serializers.CharField(
        max_length=300, required=False, allow_blank=True,
        help_text="To'liq nomi (Ingliz)"
    )
    address_uz = serializers.CharField(
        max_length=300, required=False, allow_blank=True,
        help_text="Manzil (O'zbek lotin)"
    )
    address_uz_cyrl = serializers.CharField(
        max_length=300, required=False, allow_blank=True,
        help_text="Manzil (O'zbek kirill)"
    )
    address_ru = serializers.CharField(
        max_length=300, required=False, allow_blank=True,
        help_text="Manzil (Rus)"
    )
    address_en = serializers.CharField(
        max_length=300, required=False, allow_blank=True,
        help_text="Manzil (Ingliz)"
    )
    # Umumiy maydonlar
    established_year = serializers.IntegerField(
        required=False, min_value=1900, max_value=2100,
        help_text="Tashkil etilgan yili (masalan: 2005)"
    )
    phone = serializers.CharField(
        max_length=50, required=False, allow_blank=True,
        help_text="Telefon raqami"
    )
    email = serializers.EmailField(
        required=False, allow_blank=True,
        help_text="Elektron pochta"
    )
    website = serializers.URLField(
        required=False, allow_blank=True,
        help_text="Veb-sayt manzili (https://...)"
    )
    logo = serializers.ImageField(
        required=False, allow_null=True,
        help_text="Logo rasmi (multipart/form-data)"
    )
    # Ijtimoiy tarmoqlar
    telegram = serializers.URLField(
        required=False, allow_blank=True, allow_null=True,
        help_text="Telegram kanal/guruh URL"
    )
    instagram = serializers.URLField(
        required=False, allow_blank=True, allow_null=True,
        help_text="Instagram sahifa URL"
    )
    facebook = serializers.URLField(
        required=False, allow_blank=True, allow_null=True,
        help_text="Facebook sahifa URL"
    )
    youtube = serializers.URLField(
        required=False, allow_blank=True, allow_null=True,
        help_text="YouTube kanal URL"
    )

    def validate(self, data):
        # Yaratishda (instance yo'q) kamida bitta tilda short_name va full_name shart
        if not self.instance:
            short_names = [
                data.get('short_name_uz', ''),
                data.get('short_name_ru', ''),
                data.get('short_name_en', ''),
                data.get('short_name_uz_cyrl', ''),
            ]
            full_names = [
                data.get('full_name_uz', ''),
                data.get('full_name_ru', ''),
                data.get('full_name_en', ''),
                data.get('full_name_uz_cyrl', ''),
            ]
            if not any(short_names):
                raise serializers.ValidationError(
                    "Kamida bitta tilda qisqa nom kiritilishi shart (short_name_uz, short_name_ru yoki short_name_en)."
                )
            if not any(full_names):
                raise serializers.ValidationError(
                    "Kamida bitta tilda to'liq nom kiritilishi shart (full_name_uz, full_name_ru yoki full_name_en)."
                )
        return data

    def create(self, validated_data):
        # Singleton: mavjud bo'lsa yangilaydi, yo'q bo'lsa yaratadi
        instance = SiteSettings.objects.first()
        if instance:
            for attr, value in validated_data.items():
                setattr(instance, attr, value)
            instance.save()
            return instance
        return SiteSettings.objects.create(**validated_data)

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance
