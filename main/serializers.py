from rest_framework import serializers
from .models import Statistic

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


class StatisticSerializer(serializers.Serializer):
    """
    Read serializer.
    translations — {"uz": {"label": "..."}, "ru": {"label": "..."}, ...}
    """
    id = serializers.IntegerField(read_only=True)
    key = serializers.CharField()
    value = serializers.IntegerField()
    translations = serializers.SerializerMethodField()
    icon = serializers.CharField(allow_null=True, allow_blank=True)
    sort_order = serializers.IntegerField()
    updated_at = serializers.DateTimeField(read_only=True)

    def get_translations(self, obj):
        return build_translations(obj, ['label'])


class StatisticWriteSerializer(serializers.Serializer):
    """
    Write serializer. Har bir til uchun label alohida maydon.
    Kamida bitta tilda label_* to'ldirilishi shart.
    """
    key = serializers.CharField(
        max_length=50,
        help_text="Texnik identifikator (unikal). Masalan: students_count, teachers_count"
    )
    value = serializers.IntegerField(
        min_value=0,
        help_text="Statistika qiymati (musbat son)"
    )
    label_uz = serializers.CharField(
        max_length=100, required=False, allow_blank=True,
        help_text="Yorliq (O'zbek lotin). Masalan: O'quvchilar soni"
    )
    label_uz_cyrl = serializers.CharField(
        max_length=100, required=False, allow_blank=True,
        help_text="Yorliq (O'zbek kirill)"
    )
    label_ru = serializers.CharField(
        max_length=100, required=False, allow_blank=True,
        help_text="Yorliq (Rus). Masalan: Количество учеников"
    )
    label_en = serializers.CharField(
        max_length=100, required=False, allow_blank=True,
        help_text="Yorliq (Ingliz). Masalan: Number of Students"
    )
    icon = serializers.CharField(
        max_length=100, required=False, allow_blank=True, allow_null=True,
        help_text="Icon classi. Masalan: fas fa-users"
    )
    sort_order = serializers.IntegerField(
        default=1, min_value=0,
        help_text="Tartib raqami"
    )

    def validate_key(self, value):
        qs = Statistic.objects.filter(key=value)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError(
                f"'{value}' kaliti allaqachon mavjud. Boshqa kalit tanlang."
            )
        return value

    def validate(self, data):
        if self.partial:
            instance = self.instance
            labels = [
                data.get(f'label_{l}') or (getattr(instance, f'label_{l}', '') if instance else '')
                for l in ['uz', 'ru', 'en', 'uz_cyrl']
            ]
        else:
            labels = [data.get(f'label_{l}', '') for l in ['uz', 'ru', 'en', 'uz_cyrl']]
        if not any(labels):
            raise serializers.ValidationError(
                "Kamida bitta tilda yorliq kiritilishi shart (label_uz, label_ru yoki label_en)."
            )
        return data

    def create(self, validated_data):
        return Statistic.objects.create(**validated_data)

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class StatisticBulkUpdateSerializer(serializers.Serializer):
    """Bir nechta statistikani bir vaqtda yangilash (faqat value)."""
    updates = serializers.ListField(
        child=serializers.DictField(),
        help_text='[{"key": "students_count", "value": 1200}, {"key": "teachers_count", "value": 85}]'
    )

    def validate_updates(self, value):
        if not value:
            raise serializers.ValidationError("updates bo'sh bo'lishi mumkin emas.")
        for item in value:
            if 'key' not in item:
                raise serializers.ValidationError("Har bir element 'key' maydoniga ega bo'lishi kerak.")
            if 'value' not in item:
                raise serializers.ValidationError("Har bir element 'value' maydoniga ega bo'lishi kerak.")
            try:
                v = int(item['value'])
                if v < 0:
                    raise serializers.ValidationError(f"'{item['key']}' uchun qiymat manfiy bo'lishi mumkin emas.")
            except (ValueError, TypeError):
                raise serializers.ValidationError(f"'{item['key']}' uchun qiymat butun son bo'lishi kerak.")
        return value
