from rest_framework import serializers
from .models import AdmissionInfo, AdmissionSubject, AdmissionDocument, FAQ, DarsJadvali
from core.validators import validate_document

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


# в”Ђв”Ђв”Ђ AdmissionInfo в”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђ

class AdmissionInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = AdmissionInfo
        fields = [
            'id', 'academic_year',
            'total_quota', 'grant_quota', 'contract_quota', 'contract_price',
            'application_start', 'application_end', 'exam_date', 'results_date',
            'online_apply_url', 'is_active', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class AdmissionInfoWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = AdmissionInfo
        fields = [
            'academic_year',
            'total_quota', 'grant_quota', 'contract_quota', 'contract_price',
            'application_start', 'application_end', 'exam_date', 'results_date',
            'online_apply_url', 'is_active',
        ]

    def validate(self, data):
        total = data.get('total_quota')
        grant = data.get('grant_quota')
        contract = data.get('contract_quota')
        if total and grant and contract and (grant + contract) > total:
            raise serializers.ValidationError(
                "Grant va kontrakt kvotalari yig'indisi jami kvotadan oshmasligi kerak."
            )
        start = data.get('application_start')
        end = data.get('application_end')
        exam = data.get('exam_date')
        results = data.get('results_date')
        if start and end and start > end:
            raise serializers.ValidationError(
                "Ariza qabul boshlanishi sanasi tugash sanasidan oldin bo'lishi kerak."
            )
        if exam and end and exam < end:
            raise serializers.ValidationError(
                "Imtihon sanasi ariza qabul tugash sanasidan keyin bo'lishi kerak."
            )
        if results and exam and results < exam:
            raise serializers.ValidationError(
                "Natijalar e'lon qilish sanasi imtihon sanasidan keyin bo'lishi kerak."
            )
        return data


# в”Ђв”Ђв”Ђ AdmissionSubject в”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђ

class AdmissionSubjectSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    subject_type = serializers.CharField()
    subject_type_display = serializers.SerializerMethodField()
    max_score = serializers.IntegerField()
    sort_order = serializers.IntegerField()
    translations = serializers.SerializerMethodField()

    def get_subject_type_display(self, obj):
        return obj.get_subject_type_display()

    def get_translations(self, obj):
        return build_translations(obj, ['subject_name', 'description'])


class AdmissionSubjectWriteSerializer(serializers.Serializer):
    subject_name_uz = serializers.CharField(max_length=200, required=False, allow_blank=True)
    subject_name_uz_cyrl = serializers.CharField(max_length=200, required=False, allow_blank=True)
    subject_name_ru = serializers.CharField(max_length=200, required=False, allow_blank=True)
    subject_name_en = serializers.CharField(max_length=200, required=False, allow_blank=True)
    description_uz = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    description_uz_cyrl = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    description_ru = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    description_en = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    subject_type = serializers.ChoiceField(choices=AdmissionSubject.SubjectType.choices, default='test')
    max_score = serializers.IntegerField(min_value=1)
    sort_order = serializers.IntegerField(default=0)

    def validate(self, data):
        names = [
            data.get('subject_name_uz', ''),
            data.get('subject_name_ru', ''),
            data.get('subject_name_en', ''),
            data.get('subject_name_uz_cyrl', ''),
        ]
        if not any(names):
            raise serializers.ValidationError(
                "Kamida bitta tilda fan nomi kiritilishi shart."
            )
        return data

    def create(self, validated_data):
        return AdmissionSubject.objects.create(**validated_data)

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


# в”Ђв”Ђв”Ђ AdmissionDocument в”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђ

class AdmissionDocumentSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    translations = serializers.SerializerMethodField()
    document_file = serializers.SerializerMethodField()
    is_required = serializers.BooleanField()
    sort_order = serializers.IntegerField()

    def get_translations(self, obj):
        return build_translations(obj, ['document_name', 'note'])

    def get_document_file(self, obj):
        if obj.document_file:
            request = self.context.get('request')
            return request.build_absolute_uri(obj.document_file.url) if request else obj.document_file.url
        return None


class AdmissionDocumentWriteSerializer(serializers.Serializer):
    document_name_uz = serializers.CharField(max_length=300, required=False, allow_blank=True)
    document_name_uz_cyrl = serializers.CharField(max_length=300, required=False, allow_blank=True)
    document_name_ru = serializers.CharField(max_length=300, required=False, allow_blank=True)
    document_name_en = serializers.CharField(max_length=300, required=False, allow_blank=True)
    note_uz = serializers.CharField(max_length=500, required=False, allow_blank=True, allow_null=True)
    note_uz_cyrl = serializers.CharField(max_length=500, required=False, allow_blank=True, allow_null=True)
    note_ru = serializers.CharField(max_length=500, required=False, allow_blank=True, allow_null=True)
    note_en = serializers.CharField(max_length=500, required=False, allow_blank=True, allow_null=True)
    document_file = serializers.FileField(
        required=False, allow_null=True,
        help_text="Hujjat fayli (PDF, DOCX va h.k.). Maks: 30 MB."
    )
    is_required = serializers.BooleanField(default=True)
    sort_order = serializers.IntegerField(default=0)

    def validate_document_file(self, value):
        return validate_document(value)

    def validate(self, data):
        names = [
            data.get('document_name_uz', ''),
            data.get('document_name_ru', ''),
            data.get('document_name_en', ''),
            data.get('document_name_uz_cyrl', ''),
        ]
        if not any(names):
            raise serializers.ValidationError(
                "Kamida bitta tilda hujjat nomi kiritilishi shart."
            )
        return data

    def create(self, validated_data):
        return AdmissionDocument.objects.create(**validated_data)

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


# в”Ђв”Ђв”Ђ FAQ в”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђ

class FAQSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    translations = serializers.SerializerMethodField()
    category = serializers.CharField()
    category_display = serializers.SerializerMethodField()
    is_featured = serializers.BooleanField()
    sort_order = serializers.IntegerField()
    is_active = serializers.BooleanField()

    def get_translations(self, obj):
        return build_translations(obj, ['question', 'answer'])

    def get_category_display(self, obj):
        return obj.get_category_display()


class FAQWriteSerializer(serializers.Serializer):
    question_uz = serializers.CharField(required=False, allow_blank=True)
    question_uz_cyrl = serializers.CharField(required=False, allow_blank=True)
    question_ru = serializers.CharField(required=False, allow_blank=True)
    question_en = serializers.CharField(required=False, allow_blank=True)
    answer_uz = serializers.CharField(required=False, allow_blank=True)
    answer_uz_cyrl = serializers.CharField(required=False, allow_blank=True)
    answer_ru = serializers.CharField(required=False, allow_blank=True)
    answer_en = serializers.CharField(required=False, allow_blank=True)
    category = serializers.ChoiceField(choices=FAQ.Category.choices, default='general')
    is_featured = serializers.BooleanField(default=False)
    sort_order = serializers.IntegerField(default=0)
    is_active = serializers.BooleanField(default=True)

    def validate(self, data):
        if not any([data.get('question_uz', ''), data.get('question_ru', ''),
                    data.get('question_en', ''), data.get('question_uz_cyrl', '')]):
            raise serializers.ValidationError("Kamida bitta tilda savol kiritilishi shart.")
        if not any([data.get('answer_uz', ''), data.get('answer_ru', ''),
                    data.get('answer_en', ''), data.get('answer_uz_cyrl', '')]):
            raise serializers.ValidationError("Kamida bitta tilda javob kiritilishi shart.")
        return data

    def create(self, validated_data):
        return FAQ.objects.create(**validated_data)

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


# ─────────────────────────────────────────────────────────────────────────────
# DarsJadvali
# ─────────────────────────────────────────────────────────────────────────────

class DarsJadvaliSerializer(serializers.Serializer):
    """Read serializer."""
    id = serializers.IntegerField(read_only=True)
    translations = serializers.SerializerMethodField()
    file = serializers.SerializerMethodField()
    sort_order = serializers.IntegerField()
    is_active = serializers.BooleanField()
    created_at = serializers.DateTimeField()
    updated_at = serializers.DateTimeField()

    def get_translations(self, obj):
        return build_translations(obj, ['title'])

    def get_file(self, obj):
        if obj.file:
            request = self.context.get('request')
            return request.build_absolute_uri(obj.file.url) if request else obj.file.url
        return None


class DarsJadvaliWriteSerializer(serializers.Serializer):
    """Write serializer — multipart/form-data."""
    title_uz = serializers.CharField(max_length=300, required=False, allow_blank=True)
    title_uz_cyrl = serializers.CharField(max_length=300, required=False, allow_blank=True)
    title_ru = serializers.CharField(max_length=300, required=False, allow_blank=True)
    title_en = serializers.CharField(max_length=300, required=False, allow_blank=True)
    file = serializers.FileField(
        required=False, allow_null=True,
        help_text="Jadval fayli (PDF, DOCX, XLSX). Maks: 30 MB."
    )
    sort_order = serializers.IntegerField(default=0)
    is_active = serializers.BooleanField(default=True)

    def validate_file(self, value):
        return validate_document(value)

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
            raise serializers.ValidationError("Kamida bitta tilda jadval nomi kiritilishi shart.")
        if not self.partial and not data.get('file'):
            raise serializers.ValidationError("Jadval fayli majburiy.")
        return data

    def create(self, validated_data):
        return DarsJadvali.objects.create(**validated_data)

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class AdmissionCurrentSerializer(serializers.Serializer):
    admission_info = AdmissionInfoSerializer()
    subjects = AdmissionSubjectSerializer(many=True)
    documents = AdmissionDocumentSerializer(many=True)

