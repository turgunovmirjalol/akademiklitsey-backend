from rest_framework import serializers
from .models import Circle

LANGS = ['uz', 'uz_cyrl', 'ru', 'en']


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


CIRCLE_FIELDS = ['name', 'description', 'schedule']


# ─── Read serializer ─────────────────────────────────────────────────────────

class CircleSerializer(serializers.Serializer):
    """
    Read serializer. translations dict sifatida qaytariladi:
    {"uz": {"name": "...", "description": "...", "schedule": "..."}, "ru": {...}}
    """
    id = serializers.IntegerField(read_only=True)
    slug = serializers.SlugField(read_only=True)
    translations = serializers.SerializerMethodField()
    category = serializers.CharField()
    category_display = serializers.SerializerMethodField()
    teacher = serializers.PrimaryKeyRelatedField(read_only=True, allow_null=True)
    teacher_name = serializers.SerializerMethodField()
    max_students = serializers.IntegerField(allow_null=True)
    current_students = serializers.IntegerField()
    available_slots = serializers.SerializerMethodField()
    is_full = serializers.BooleanField(read_only=True)
    room = serializers.CharField(allow_null=True, allow_blank=True)
    photo = serializers.SerializerMethodField()
    is_active = serializers.BooleanField()
    sort_order = serializers.IntegerField()

    def get_translations(self, obj):
        return build_translations(obj, CIRCLE_FIELDS)

    def get_category_display(self, obj):
        return obj.get_category_display()

    def get_teacher_name(self, obj):
        return obj.teacher.full_name if obj.teacher else None

    def get_available_slots(self, obj):
        return obj.available_slots

    def get_photo(self, obj):
        if obj.photo:
            request = self.context.get('request')
            return request.build_absolute_uri(obj.photo.url) if request else obj.photo.url
        return None


# ─── Write serializer ────────────────────────────────────────────────────────

class CircleWriteSerializer(serializers.Serializer):
    """
    Write serializer. Har bir til maydoni alohida flat field.
    Rasm yuklash uchun multipart/form-data ishlatiladi.
    Kamida bitta tilda name_* to'ldirilishi shart.
    """
    # Tarjima maydonlari
    name_uz = serializers.CharField(
        max_length=200, required=False, allow_blank=True,
        help_text="To'garak nomi (O'zbek lotin)"
    )
    name_uz_cyrl = serializers.CharField(
        max_length=200, required=False, allow_blank=True,
        help_text="To'garak nomi (O'zbek kirill)"
    )
    name_ru = serializers.CharField(
        max_length=200, required=False, allow_blank=True,
        help_text="To'garak nomi (Rus)"
    )
    name_en = serializers.CharField(
        max_length=200, required=False, allow_blank=True,
        help_text="To'garak nomi (Ingliz)"
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
    schedule_uz = serializers.CharField(
        max_length=300, required=False, allow_blank=True, allow_null=True,
        help_text="Dars vaqti (O'zbek lotin). Masalan: Dushanba, Chorshanba 15:00-17:00"
    )
    schedule_uz_cyrl = serializers.CharField(
        max_length=300, required=False, allow_blank=True, allow_null=True,
        help_text="Dars vaqti (O'zbek kirill)"
    )
    schedule_ru = serializers.CharField(
        max_length=300, required=False, allow_blank=True, allow_null=True,
        help_text="Dars vaqti (Rus)"
    )
    schedule_en = serializers.CharField(
        max_length=300, required=False, allow_blank=True, allow_null=True,
        help_text="Dars vaqti (Ingliz)"
    )
    # Umumiy maydonlar
    category = serializers.ChoiceField(
        choices=Circle.Category.choices,
        default=Circle.Category.OTHER,
        help_text="sport | art | science | language | tech | other"
    )
    teacher = serializers.IntegerField(
        required=False, allow_null=True,
        help_text="Rahbar o'qituvchi ID si (ixtiyoriy)"
    )

    def get_fields(self):
        fields = super().get_fields()
        return fields
    max_students = serializers.IntegerField(
        required=False, allow_null=True, min_value=1,
        help_text="Maksimal o'quvchilar soni (ixtiyoriy)"
    )
    current_students = serializers.IntegerField(
        default=0, min_value=0,
        help_text="Hozirgi o'quvchilar soni"
    )
    room = serializers.CharField(
        max_length=50, required=False, allow_blank=True, allow_null=True,
        help_text="Xona raqami (ixtiyoriy)"
    )
    photo = serializers.ImageField(
        required=False, allow_null=True,
        help_text="To'garak rasmi (ixtiyoriy, multipart/form-data)"
    )
    is_active = serializers.BooleanField(default=True)
    sort_order = serializers.IntegerField(default=0)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def validate_teacher(self, value):
        if value is None:
            return None
        from structure.models import Teacher
        try:
            return Teacher.objects.get(pk=value, is_active=True)
        except Teacher.DoesNotExist:
            raise serializers.ValidationError(
                f"ID={value} bo'lgan faol o'qituvchi topilmadi."
            )

    def validate(self, data):
        names = [
            data.get('name_uz', ''),
            data.get('name_ru', ''),
            data.get('name_en', ''),
            data.get('name_uz_cyrl', ''),
        ]
        if not any(names):
            raise serializers.ValidationError(
                "Kamida bitta tilda to'garak nomi kiritilishi shart (name_uz, name_ru yoki name_en)."
            )
        max_s = data.get('max_students')
        cur_s = data.get('current_students', 0)
        if max_s is not None and cur_s > max_s:
            raise serializers.ValidationError(
                "Hozirgi o'quvchilar soni maksimal o'rinlar sonidan oshmasligi kerak."
            )
        return data

    def create(self, validated_data):
        return Circle.objects.create(**validated_data)

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance
