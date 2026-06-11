from rest_framework import serializers
from .models import LibraryResource, LibraryStats
from core.validators import validate_image, validate_document

LANGS = ['uz', 'uz_cyrl', 'ru', 'en']


def build_translations(obj, fields: list) -> dict:
    result = {}
    for lang in LANGS:
        data = {}
        for field in fields:
            val = getattr(obj, f"{field}_{lang}", None)
            data[field] = val if val is not None else ''
        result[lang] = data
    return result


def apply_lang_filter(serializer_data, lang: str):
    if not lang or lang not in LANGS:
        return serializer_data

    def _filter(item):
        if not isinstance(item, dict) or 'translations' not in item:
            return item
        t = item.get('translations') or {}
        chosen = t.get(lang, {})
        if not any(chosen.values()):
            chosen = t.get('uz', {})
        item = dict(item)
        item['translations'] = {lang: chosen}
        return item

    if isinstance(serializer_data, list):
        return [_filter(i) for i in serializer_data]
    return _filter(serializer_data)


# ─────────────────────────────────────────────────────────────────────────────
# LibraryStats
# ─────────────────────────────────────────────────────────────────────────────

class LibraryStatsSerializer(serializers.ModelSerializer):
    class Meta:
        model = LibraryStats
        fields = [
            'id',
            'books_count', 'books_suffix',
            'electronic_resources_count', 'electronic_resources_suffix',
            'journals_count', 'journals_suffix',
            'manuals_count', 'manuals_suffix',
            'updated_at',
        ]
        read_only_fields = ['id', 'updated_at']


class LibraryStatsWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = LibraryStats
        fields = [
            'books_count', 'books_suffix',
            'electronic_resources_count', 'electronic_resources_suffix',
            'journals_count', 'journals_suffix',
            'manuals_count', 'manuals_suffix',
        ]


# ─────────────────────────────────────────────────────────────────────────────
# LibraryResource — Read
# ─────────────────────────────────────────────────────────────────────────────

class LibraryResourceSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    translations = serializers.SerializerMethodField()
    author = serializers.CharField()
    category = serializers.CharField()
    category_display = serializers.SerializerMethodField()
    file_type = serializers.CharField()
    file_type_display = serializers.SerializerMethodField()
    file = serializers.SerializerMethodField()
    cover_image = serializers.SerializerMethodField()
    is_featured = serializers.BooleanField()
    is_active = serializers.BooleanField()
    sort_order = serializers.IntegerField()
    download_count = serializers.IntegerField()
    created_at = serializers.DateTimeField()
    updated_at = serializers.DateTimeField()

    def get_translations(self, obj):
        return build_translations(obj, ['title', 'description'])

    def get_category_display(self, obj):
        return obj.get_category_display()

    def get_file_type_display(self, obj):
        return obj.get_file_type_display()

    def get_file(self, obj):
        if obj.file:
            request = self.context.get('request')
            return request.build_absolute_uri(obj.file.url) if request else obj.file.url
        return None

    def get_cover_image(self, obj):
        if obj.cover_image:
            request = self.context.get('request')
            return request.build_absolute_uri(obj.cover_image.url) if request else obj.cover_image.url
        return None


# ─────────────────────────────────────────────────────────────────────────────
# LibraryResource — Write
# ─────────────────────────────────────────────────────────────────────────────

class LibraryResourceWriteSerializer(serializers.Serializer):
    title_uz = serializers.CharField(max_length=300, required=False, allow_blank=True, help_text="Nomi (UZ)")
    title_uz_cyrl = serializers.CharField(max_length=300, required=False, allow_blank=True, help_text="Nomi (UZ Kirill)")
    title_ru = serializers.CharField(max_length=300, required=False, allow_blank=True, help_text="Nomi (RU)")
    title_en = serializers.CharField(max_length=300, required=False, allow_blank=True, help_text="Nomi (EN)")

    description_uz = serializers.CharField(required=False, allow_blank=True, help_text="Tavsif (UZ)")
    description_uz_cyrl = serializers.CharField(required=False, allow_blank=True, help_text="Tavsif (UZ Kirill)")
    description_ru = serializers.CharField(required=False, allow_blank=True, help_text="Tavsif (RU)")
    description_en = serializers.CharField(required=False, allow_blank=True, help_text="Tavsif (EN)")

    author = serializers.CharField(max_length=300, required=False, allow_blank=True, help_text="Muallif")
    category = serializers.ChoiceField(choices=LibraryResource.Category.choices, default=LibraryResource.Category.DARSLIK)
    file_type = serializers.ChoiceField(choices=LibraryResource.FileType.choices, default=LibraryResource.FileType.PDF)
    file = serializers.FileField(required=False, allow_null=True, help_text="Resurs fayli (PDF, DOCX va h.k.). Maks: 30 MB.")
    cover_image = serializers.ImageField(required=False, allow_null=True, help_text="Muqova rasmi. Maks: 8 MB.")
    is_featured = serializers.BooleanField(default=False)
    is_active = serializers.BooleanField(default=True)
    sort_order = serializers.IntegerField(default=0)

    def validate_file(self, value):
        return validate_document(value)

    def validate_cover_image(self, value):
        return validate_image(value)

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
                "Kamida bitta tilda resurs nomi kiritilishi shart (title_uz, title_ru yoki title_en)."
            )
        return data

    def create(self, validated_data):
        return LibraryResource.objects.create(**validated_data)

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance
