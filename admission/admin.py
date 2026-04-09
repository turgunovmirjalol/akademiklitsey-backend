from django.contrib import admin, messages
from django.utils.html import format_html, mark_safe
from django import forms
from datetime import date
from .models import AdmissionInfo, AdmissionSubject, AdmissionDocument, FAQ


# ─────────────────────────────────────────────────────────────────────────────
# AdmissionInfo
# ─────────────────────────────────────────────────────────────────────────────

class AdmissionInfoAdminForm(forms.ModelForm):
    class Meta:
        model = AdmissionInfo
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from django.utils import timezone
        year = timezone.now().year
        self.fields['academic_year'].help_text = (
            f"Format: YYYY-YYYY (masalan: {year}-{year + 1})"
        )
        self.fields['online_apply_url'].help_text = "Onlayn ariza to'ldirish sahifasining URL manzili"

    def clean_academic_year(self):
        from django.utils import timezone
        value = self.cleaned_data.get('academic_year', '')
        # Faqat yangi yozuv uchun yil tekshiruvi
        if value and not self.instance.pk:
            current_year = timezone.now().year
            try:
                year_part = int(value.split('-')[0])
                if year_part != current_year:
                    raise forms.ValidationError(
                        f"O'quv yili joriy yil ({current_year}) bilan boshlanishi kerak. "
                        f"Masalan: {current_year}-{current_year + 1}"
                    )
            except (ValueError, IndexError):
                raise forms.ValidationError(
                    "Noto'g'ri format. To'g'ri format: 2025-2026"
                )
        return value

    def clean(self):
        cleaned_data = super().clean()
        # Kvota tekshiruvi
        total = cleaned_data.get('total_quota')
        grant = cleaned_data.get('grant_quota')
        contract = cleaned_data.get('contract_quota')
        if total and grant and contract:
            if grant + contract > total:
                raise forms.ValidationError(
                    "Grant va kontrakt kvotalari yig'indisi jami kvotadan oshmasligi kerak."
                )
        # Sana tekshiruvlari
        start = cleaned_data.get('application_start')
        end = cleaned_data.get('application_end')
        exam = cleaned_data.get('exam_date')
        results = cleaned_data.get('results_date')
        if start and end and start > end:
            raise forms.ValidationError(
                "Ariza qabul boshlanishi sanasi tugash sanasidan oldin bo'lishi kerak."
            )
        if exam and end and exam < end:
            raise forms.ValidationError(
                "Imtihon sanasi ariza qabul tugash sanasidan keyin bo'lishi kerak."
            )
        if results and exam and results < exam:
            raise forms.ValidationError(
                "Natijalar e'lon qilish sanasi imtihon sanasidan keyin bo'lishi kerak."
            )
        # Faollik yagonaligi
        is_active = cleaned_data.get('is_active')
        if is_active:
            qs = AdmissionInfo.objects.filter(is_active=True)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise forms.ValidationError({
                    'is_active': (
                        "Faol bo'lgan boshqa qabul ma'lumoti allaqachon mavjud. "
                        "Avval uni nofaol qiling."
                    )
                })
        return cleaned_data


@admin.register(AdmissionInfo)
class AdmissionInfoAdmin(admin.ModelAdmin):
    form = AdmissionInfoAdminForm
    list_display = [
        'academic_year', 'total_quota', 'grant_quota', 'contract_quota',
        'contract_price', 'application_start', 'application_end', 'is_active', 'status_badge',
    ]
    list_filter = ['is_active']
    search_fields = ['academic_year']
    list_editable = ['is_active']
    ordering = ['-academic_year']
    readonly_fields = ['created_at', 'updated_at', 'status_badge']
    actions = ['deactivate_expired_action']

    fieldsets = (
        ("Asosiy ma'lumotlar", {
            'fields': ('academic_year', 'is_active', 'status_badge'),
        }),
        ('Kvotalar', {
            'fields': ('total_quota', 'grant_quota', 'contract_quota', 'contract_price'),
            'description': "Jami o'rinlar = grant + kontrakt bo'lishi kerak.",
        }),
        ('Muhim sanalar', {
            'fields': ('application_start', 'application_end', 'exam_date', 'results_date'),
        }),
        ("Qo'shimcha", {
            'fields': ('online_apply_url',),
        }),
        ("Tizim ma'lumotlari", {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    def status_badge(self, obj):
        if not obj.pk:
            return '—'
        if not obj.is_active:
            color, label = '#dc3545', 'Nofaol'
        elif obj.application_end and obj.application_end < date.today():
            color, label = '#fd7e14', 'Muddati tugagan'
        else:
            color, label = '#28a745', 'Faol'
        return format_html(
            '<span style="background:{};color:#fff;padding:2px 10px;border-radius:4px;">{}</span>',
            color, label,
        )
    status_badge.short_description = 'Holat'

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        if obj.application_end and obj.application_end < date.today() and not obj.is_active:
            messages.warning(
                request,
                f"'{obj.academic_year}' qabul muddati tugaganligi sababli avtomatik nofaol qilindi.",
            )

    @admin.action(description="Muddati tugaganlarni nofaol qilish")
    def deactivate_expired_action(self, request, queryset):
        count = queryset.filter(
            is_active=True, application_end__lt=date.today()
        ).update(is_active=False)
        level = messages.SUCCESS if count else messages.INFO
        msg = (
            f"{count} ta muddati tugagan qabul nofaol qilindi."
            if count else "Muddati tugagan faol qabul topilmadi."
        )
        self.message_user(request, msg, level)


# ─────────────────────────────────────────────────────────────────────────────
# AdmissionSubject
# ─────────────────────────────────────────────────────────────────────────────

@admin.register(AdmissionSubject)
class AdmissionSubjectAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'subject_type', 'max_score', 'sort_order']
    list_filter = ['subject_type']
    search_fields = ['subject_name_uz', 'subject_name_ru', 'subject_name_en']
    list_editable = ['sort_order']
    ordering = ['sort_order']

    fieldsets = (
        ("O'zbek tili (Lotin)", {
            'fields': ('subject_name_uz', 'description_uz'),
        }),
        ("O'zbek tili (Kirill)", {
            'fields': ('subject_name_uz_cyrl', 'description_uz_cyrl'),
            'classes': ('collapse',),
        }),
        ("Rus tili", {
            'fields': ('subject_name_ru', 'description_ru'),
            'classes': ('collapse',),
        }),
        ("Ingliz tili", {
            'fields': ('subject_name_en', 'description_en'),
            'classes': ('collapse',),
        }),
        ("Asosiy sozlamalar", {
            'fields': ('subject_type', 'max_score', 'sort_order'),
        }),
    )

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        form.base_fields['subject_name_uz'].required = True
        return form


# ─────────────────────────────────────────────────────────────────────────────
# AdmissionDocument
# ─────────────────────────────────────────────────────────────────────────────

@admin.register(AdmissionDocument)
class AdmissionDocumentAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'is_required', 'has_file', 'sort_order']
    list_filter = ['is_required']
    search_fields = ['document_name_uz', 'document_name_ru', 'document_name_en']
    list_editable = ['is_required', 'sort_order']
    ordering = ['sort_order']

    fieldsets = (
        ("O'zbek tili (Lotin)", {
            'fields': ('document_name_uz', 'note_uz'),
        }),
        ("O'zbek tili (Kirill)", {
            'fields': ('document_name_uz_cyrl', 'note_uz_cyrl'),
            'classes': ('collapse',),
        }),
        ("Rus tili", {
            'fields': ('document_name_ru', 'note_ru'),
            'classes': ('collapse',),
        }),
        ("Ingliz tili", {
            'fields': ('document_name_en', 'note_en'),
            'classes': ('collapse',),
        }),
        ("Fayl va sozlamalar", {
            'fields': ('document_file', 'is_required', 'sort_order'),
        }),
    )

    def has_file(self, obj):
        if obj.document_file:
            return mark_safe('<span style="color:green;">✔ Fayl bor</span>')
        return mark_safe('<span style="color:#999;">— Fayl yo\'q</span>')
    has_file.short_description = 'Fayl'

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        form.base_fields['document_name_uz'].required = True
        return form


# ─────────────────────────────────────────────────────────────────────────────
# FAQ
# ─────────────────────────────────────────────────────────────────────────────

@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    list_display = ['short_question', 'category', 'is_featured', 'is_active', 'sort_order']
    list_filter = ['category', 'is_featured', 'is_active']
    search_fields = ['question_uz', 'question_ru', 'question_en', 'answer_uz']
    list_editable = ['is_featured', 'is_active', 'sort_order']
    ordering = ['sort_order']

    fieldsets = (
        ("O'zbek tili (Lotin)", {
            'fields': ('question_uz', 'answer_uz'),
        }),
        ("O'zbek tili (Kirill)", {
            'fields': ('question_uz_cyrl', 'answer_uz_cyrl'),
            'classes': ('collapse',),
        }),
        ("Rus tili", {
            'fields': ('question_ru', 'answer_ru'),
            'classes': ('collapse',),
        }),
        ("Ingliz tili", {
            'fields': ('question_en', 'answer_en'),
            'classes': ('collapse',),
        }),
        ("Sozlamalar", {
            'fields': ('category', 'is_featured', 'is_active', 'sort_order'),
        }),
    )

    def short_question(self, obj):
        q = obj.question_uz or obj.question_ru or obj.question_en or '—'
        return q[:80] + ('...' if len(q) > 80 else '')
    short_question.short_description = 'Savol'

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        form.base_fields['question_uz'].required = True
        form.base_fields['answer_uz'].required = True
        return form
