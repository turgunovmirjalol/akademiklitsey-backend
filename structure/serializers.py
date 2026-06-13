from rest_framework import serializers
from .models import Department, Teacher, Management
from core.validators import validate_image

LANGS = ['uz', 'ru']


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
# Teacher
# ─────────────────────────────────────────────────────────────────────────────

class TeacherSerializer(serializers.Serializer):
    """Read serializer — ro'yxat uchun."""
    id = serializers.IntegerField(read_only=True)
    full_name = serializers.CharField()
    slug = serializers.SlugField(read_only=True)
    translations = serializers.SerializerMethodField()
    academic_degree = serializers.CharField(allow_null=True, allow_blank=True)
    academic_rank = serializers.CharField(allow_null=True, allow_blank=True)
    category = serializers.CharField()
    category_display = serializers.SerializerMethodField()
    experience_years = serializers.IntegerField(allow_null=True)
    department = serializers.PrimaryKeyRelatedField(read_only=True, allow_null=True)
    department_name = serializers.SerializerMethodField()
    photo = serializers.SerializerMethodField()
    email = serializers.EmailField(allow_null=True, allow_blank=True)
    sort_order = serializers.IntegerField()
    is_active = serializers.BooleanField()
    created_at = serializers.DateTimeField(read_only=True)

    def get_translations(self, obj):
        return build_translations(obj, ['position', 'subject', 'bio', 'achievements'])

    def get_category_display(self, obj):
        return obj.get_category_display()

    def get_department_name(self, obj):
        if obj.department:
            return obj.department.name_uz or obj.department.name_ru or ''
        return None

    def get_photo(self, obj):
        if obj.photo:
            request = self.context.get('request')
            return request.build_absolute_uri(obj.photo.url) if request else obj.photo.url
        return None


class TeacherWriteSerializer(serializers.Serializer):
    """
    Write serializer. Har bir til maydoni alohida flat field.
    photo — multipart/form-data orqali yuboriladi.
    Kamida bitta tilda position_* to'ldirilishi shart.
    """
    full_name = serializers.CharField(max_length=200, help_text="To'liq ismi (majburiy)")

    # Tarjima maydonlari
    position_uz = serializers.CharField(max_length=200, required=False, allow_blank=True, help_text="Lavozimi (UZ)")
    position_ru = serializers.CharField(max_length=200, required=False, allow_blank=True, help_text="Lavozimi (RU)")

    subject_uz = serializers.CharField(max_length=200, required=False, allow_blank=True, help_text="O'qitadigan fan (UZ)")
    subject_ru = serializers.CharField(max_length=200, required=False, allow_blank=True, help_text="O'qitadigan fan (RU)")

    bio_uz = serializers.CharField(required=False, allow_blank=True, allow_null=True, help_text="Tarjimai hol (UZ)")
    bio_ru = serializers.CharField(required=False, allow_blank=True, allow_null=True, help_text="Tarjimai hol (RU)")

    achievements_uz = serializers.CharField(required=False, allow_blank=True, allow_null=True, help_text="Yutuqlar (UZ)")
    achievements_ru = serializers.CharField(required=False, allow_blank=True, allow_null=True, help_text="Yutuqlar (RU)")

    # Umumiy maydonlar
    academic_degree = serializers.CharField(max_length=255, required=False, allow_blank=True, allow_null=True)
    academic_rank = serializers.CharField(max_length=255, required=False, allow_blank=True, allow_null=True)
    category = serializers.ChoiceField(choices=Teacher.Category.choices, default=Teacher.Category.NONE)
    experience_years = serializers.IntegerField(required=False, allow_null=True, min_value=0)
    department = serializers.IntegerField(required=False, allow_null=True, help_text="Kafedra ID si")
    photo = serializers.ImageField(required=False, allow_null=True, help_text="Rasm (multipart/form-data). Maks: 8 MB.")
    email = serializers.EmailField(required=False, allow_blank=True, allow_null=True)
    is_active = serializers.BooleanField(default=True)
    sort_order = serializers.IntegerField(default=0)

    def validate_department(self, value):
        if value is None:
            return None
        try:
            return Department.objects.get(pk=value)
        except Department.DoesNotExist:
            raise serializers.ValidationError(f"ID={value} bo'lgan kafedra topilmadi.")

    def validate_photo(self, value):
        return validate_image(value)

    def validate(self, data):
        # PATCH (partial=True) da mavjud instance ni ham hisobga olamiz
        if not self.partial:
            positions = [data.get(f'position_{l}', '') for l in ['uz', 'ru']]
            if not any(positions):
                raise serializers.ValidationError(
                    "Kamida bitta tilda lavozim kiritilishi shart (position_uz yoki position_ru)."
                )
        else:
            instance = self.instance
            positions = [
                data.get(f'position_{l}') or (getattr(instance, f'position_{l}', '') if instance else '')
                for l in ['uz', 'ru']
            ]
            if not any(positions):
                raise serializers.ValidationError(
                    "Kamida bitta tilda lavozim kiritilishi shart (position_uz yoki position_ru)."
                )
        return data

    def create(self, validated_data):
        return Teacher.objects.create(**validated_data)

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


# ─────────────────────────────────────────────────────────────────────────────
# Department
# ─────────────────────────────────────────────────────────────────────────────

class DepartmentSerializer(serializers.Serializer):
    """Read serializer — ro'yxat uchun."""
    id = serializers.IntegerField(read_only=True)
    slug = serializers.SlugField(read_only=True)
    translations = serializers.SerializerMethodField()
    head_teacher = serializers.SerializerMethodField()
    subjects = serializers.ListField(child=serializers.CharField(), allow_null=True)
    room_number = serializers.CharField(allow_null=True, allow_blank=True)
    phone = serializers.CharField(allow_null=True, allow_blank=True)
    email = serializers.EmailField(allow_null=True, allow_blank=True)
    teachers_count = serializers.IntegerField(read_only=True)
    sort_order = serializers.IntegerField()
    is_active = serializers.BooleanField()
    created_at = serializers.DateTimeField(read_only=True)

    def get_translations(self, obj):
        return build_translations(obj, ['name', 'description'])

    def get_head_teacher(self, obj):
        if obj.head_teacher:
            return {
                'id': obj.head_teacher.id,
                'full_name': obj.head_teacher.full_name,
                'position': obj.head_teacher.position_uz or obj.head_teacher.position_ru or '',
            }
        return None


class DepartmentDetailSerializer(DepartmentSerializer):
    """Read serializer — detail uchun (o'qituvchilar bilan)."""
    teachers = serializers.SerializerMethodField()

    def get_teachers(self, obj):
        teachers = obj.teachers.filter(is_active=True).order_by('sort_order', 'full_name')
        return TeacherSerializer(teachers, many=True, context=self.context).data


class DepartmentWriteSerializer(serializers.Serializer):
    """Write serializer. Kamida bitta tilda name_* to'ldirilishi shart."""
    name_uz = serializers.CharField(max_length=200, required=False, allow_blank=True, help_text="Nomi (UZ)")
    name_ru = serializers.CharField(max_length=200, required=False, allow_blank=True, help_text="Nomi (RU)")

    description_uz = serializers.CharField(required=False, allow_blank=True, allow_null=True, help_text="Tavsif (UZ)")
    description_ru = serializers.CharField(required=False, allow_blank=True, allow_null=True, help_text="Tavsif (RU)")

    head_teacher = serializers.IntegerField(required=False, allow_null=True, help_text="Kafedra mudiri ID si")
    subjects = serializers.ListField(child=serializers.CharField(), required=False, allow_null=True, help_text="Fanlar ro'yxati")
    room_number = serializers.CharField(max_length=20, required=False, allow_blank=True, allow_null=True)
    phone = serializers.CharField(max_length=20, required=False, allow_blank=True, allow_null=True)
    email = serializers.EmailField(required=False, allow_blank=True, allow_null=True)
    sort_order = serializers.IntegerField(default=0)
    is_active = serializers.BooleanField(default=True)

    def validate_head_teacher(self, value):
        if value is None:
            return None
        try:
            return Teacher.objects.get(pk=value, is_active=True)
        except Teacher.DoesNotExist:
            raise serializers.ValidationError(f"ID={value} bo'lgan faol o'qituvchi topilmadi.")

    def validate(self, data):
        if not self.partial:
            names = [data.get(f'name_{l}', '') for l in ['uz', 'ru']]
            if not any(names):
                raise serializers.ValidationError(
                    "Kamida bitta tilda kafedra nomi kiritilishi shart (name_uz yoki name_ru)."
                )
        else:
            instance = self.instance
            names = [
                data.get(f'name_{l}') or (getattr(instance, f'name_{l}', '') if instance else '')
                for l in ['uz', 'ru']
            ]
            if not any(names):
                raise serializers.ValidationError(
                    "Kamida bitta tilda kafedra nomi kiritilishi shart (name_uz yoki name_ru)."
                )
        return data

    def create(self, validated_data):
        return Department.objects.create(**validated_data)

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


# ─────────────────────────────────────────────────────────────────────────────
# Management
# ─────────────────────────────────────────────────────────────────────────────

class ManagementSerializer(serializers.Serializer):
    """Read serializer."""
    id = serializers.IntegerField(read_only=True)
    full_name = serializers.CharField()
    translations = serializers.SerializerMethodField()
    academic_degree = serializers.CharField(allow_null=True, allow_blank=True)
    phone = serializers.CharField(allow_null=True, allow_blank=True)
    email = serializers.EmailField(allow_null=True, allow_blank=True)
    photo = serializers.SerializerMethodField()
    sort_order = serializers.IntegerField()
    is_active = serializers.BooleanField()

    def get_translations(self, obj):
        return build_translations(obj, ['position', 'bio', 'reception_hours'])

    def get_photo(self, obj):
        if obj.photo:
            request = self.context.get('request')
            return request.build_absolute_uri(obj.photo.url) if request else obj.photo.url
        return None


class ManagementWriteSerializer(serializers.Serializer):
    """Write serializer. Kamida bitta tilda position_* to'ldirilishi shart."""
    full_name = serializers.CharField(max_length=200, help_text="To'liq ismi (majburiy)")

    position_uz = serializers.CharField(max_length=200, required=False, allow_blank=True, help_text="Lavozimi (UZ)")
    position_ru = serializers.CharField(max_length=200, required=False, allow_blank=True, help_text="Lavozimi (RU)")

    bio_uz = serializers.CharField(required=False, allow_blank=True, allow_null=True, help_text="Tarjimai hol (UZ)")
    bio_ru = serializers.CharField(required=False, allow_blank=True, allow_null=True, help_text="Tarjimai hol (RU)")

    reception_hours_uz = serializers.CharField(max_length=200, required=False, allow_blank=True, allow_null=True, help_text="Qabul vaqti (UZ)")
    reception_hours_ru = serializers.CharField(max_length=200, required=False, allow_blank=True, allow_null=True, help_text="Qabul vaqti (RU)")

    academic_degree = serializers.CharField(max_length=100, required=False, allow_blank=True, allow_null=True)
    phone = serializers.CharField(max_length=20, required=False, allow_blank=True, allow_null=True)
    email = serializers.EmailField(required=False, allow_blank=True, allow_null=True)
    photo = serializers.ImageField(required=False, allow_null=True, help_text="Rasm (multipart/form-data). Maks: 8 MB.")
    sort_order = serializers.IntegerField(default=0)
    is_active = serializers.BooleanField(default=True)

    def validate_photo(self, value):
        return validate_image(value)

    def validate(self, data):
        if not self.partial:
            positions = [data.get(f'position_{l}', '') for l in ['uz', 'ru']]
            if not any(positions):
                raise serializers.ValidationError(
                    "Kamida bitta tilda lavozim kiritilishi shart (position_uz yoki position_ru)."
                )
        else:
            instance = self.instance
            positions = [
                data.get(f'position_{l}') or (getattr(instance, f'position_{l}', '') if instance else '')
                for l in ['uz', 'ru']
            ]
            if not any(positions):
                raise serializers.ValidationError(
                    "Kamida bitta tilda lavozim kiritilishi shart (position_uz yoki position_ru)."
                )
        return data

    def create(self, validated_data):
        return Management.objects.create(**validated_data)

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance
