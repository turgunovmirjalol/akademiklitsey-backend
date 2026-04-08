from rest_framework import serializers
from django.utils.text import slugify
from .models import Department, Teacher, Management


class DepartmentSerializer(serializers.ModelSerializer):
    """Kafedralar uchun serializer"""
    head_teacher = serializers.SerializerMethodField()
    teachers_count = serializers.ReadOnlyField()
    
    class Meta:
        model = Department
        fields = [
            'id', 'name', 'slug', 'description', 'head_teacher', 
            'subjects', 'room_number', 'phone', 'email', 
            'teachers_count', 'sort_order', 'is_active', 'created_at'
        ]
        read_only_fields = ['id', 'teachers_count', 'created_at']
    
    def get_head_teacher(self, obj):
        """Kafedra mudiri ma'lumotlari"""
        if obj.head_teacher:
            return {
                'id': obj.head_teacher.id,
                'full_name': obj.head_teacher.full_name,
                'position': obj.head_teacher.position
            }
        return None


class DepartmentDetailSerializer(DepartmentSerializer):
    """Kafedra detallari uchun serializer (o'qituvchilar ro'yxati bilan)"""
    teachers = serializers.SerializerMethodField()
    
    class Meta(DepartmentSerializer.Meta):
        fields = DepartmentSerializer.Meta.fields + ['teachers']
    
    def get_teachers(self, obj):
        """Kafedraga tegishli o'qituvchilar ro'yxati"""
        teachers = obj.teachers.filter(is_active=True).order_by('sort_order', 'full_name')
        return TeacherListSerializer(teachers, many=True).data


class DepartmentWriteSerializer(serializers.ModelSerializer):
    """Kafedra yaratish/tahrirlash uchun serializer"""
    
    class Meta:
        model = Department
        fields = [
            'name', 'slug', 'description', 'head_teacher', 
            'subjects', 'room_number', 'phone', 'email', 
            'sort_order', 'is_active'
        ]
    
    def validate_slug(self, value):
        """Slugning noyobligini tekshirish"""
        if self.instance and self.instance.slug != value:
            if Department.objects.filter(slug=value).exists():
                raise serializers.ValidationError("Bu slug allaqachon mavjud!")
        elif not self.instance and Department.objects.filter(slug=value).exists():
            raise serializers.ValidationError("Bu slug allaqachon mavjud!")
        return value
    
    def create(self, validated_data):
        """Kafedra yaratishda slug avtomatik yaratish"""
        if 'slug' not in validated_data or not validated_data['slug']:
            validated_data['slug'] = slugify(validated_data['name'])
        return super().create(validated_data)
    
    def update(self, instance, validated_data):
        """Kafedrani yangilash - slug bo'sh bo'lsa name dan yaratish"""
        if 'slug' in validated_data and (not validated_data['slug'] or validated_data['slug'].strip() == ''):
            validated_data['slug'] = slugify(validated_data.get('name', instance.name))
        return super().update(instance, validated_data)


class TeacherListSerializer(serializers.ModelSerializer):
    """O'qituvchilar ro'yxati uchun serializer"""
    department = serializers.SerializerMethodField()
    category_display = serializers.CharField(source='get_category_display', read_only=True)
    photo_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Teacher
        fields = [
            'id', 'full_name', 'slug', 'position', 'academic_degree', 
            'academic_rank', 'category', 'category_display', 'experience_years',
            'subject', 'department', 'photo', 'photo_url', 'email', 'sort_order'
        ]
    
    def get_department(self, obj):
        """O'qituvchi kafedrasi ma'lumotlari"""
        if obj.department:
            return {
                'id': obj.department.id,
                'name': obj.department.name,
                'slug': obj.department.slug
            }
        return None
    
    def get_photo_url(self, obj):
        """Rasm URL ni olish"""
        if obj.photo:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.photo.url)
            return obj.photo.url
        return None


class TeacherDetailSerializer(TeacherListSerializer):
    """O'qituvchi detallari uchun serializer"""
    
    class Meta(TeacherListSerializer.Meta):
        fields = TeacherListSerializer.Meta.fields + ['bio', 'achievements', 'created_at']


class TeacherWriteSerializer(serializers.ModelSerializer):
    """O'qituvchi yaratish/tahrirlash uchun serializer"""
    
    class Meta:
        model = Teacher
        fields = [
            'full_name', 'slug', 'position', 'academic_degree', 'academic_rank',
            'category', 'experience_years', 'subject', 'department', 
            'photo', 'bio', 'achievements', 'email', 'is_active', 'sort_order'
        ]
        extra_kwargs = {
            'photo': {'required': False}
        }
    
    def validate_slug(self, value):
        """Slugning noyobligini tekshirish"""
        if self.instance and self.instance.slug != value:
            if Teacher.objects.filter(slug=value).exists():
                raise serializers.ValidationError("Bu slug allaqachon mavjud!")
        elif not self.instance and Teacher.objects.filter(slug=value).exists():
            raise serializers.ValidationError("Bu slug allaqachon mavjud!")
        return value
    
    def create(self, validated_data):
        """O'qituvchi yaratishda slug avtomatik yaratish"""
        if 'slug' not in validated_data or not validated_data['slug']:
            validated_data['slug'] = slugify(validated_data['full_name'])
        return super().create(validated_data)
    
    def update(self, instance, validated_data):
        """O'qituvchini yangilash - slug bo'sh bo'lsa full_name dan yaratish"""
        if 'slug' in validated_data and (not validated_data['slug'] or validated_data['slug'].strip() == ''):
            validated_data['slug'] = slugify(validated_data.get('full_name', instance.full_name))
        return super().update(instance, validated_data)


class ManagementSerializer(serializers.ModelSerializer):
    """Rahbariyat uchun serializer"""
    photo_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Management
        fields = [
            'id', 'full_name', 'position', 'academic_degree', 
            'phone', 'email', 'reception_hours', 'photo', 'photo_url', 'bio', 
            'sort_order', 'is_active'
        ]
    
    def get_photo_url(self, obj):
        """Rasm URL ni olish"""
        if obj.photo:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.photo.url)
            return obj.photo.url
        return None


class ManagementWriteSerializer(serializers.ModelSerializer):
    """Rahbariyat yaratish/tahrirlash uchun serializer"""
    
    class Meta:
        model = Management
        fields = [
            'full_name', 'position', 'academic_degree', 
            'phone', 'email', 'reception_hours', 'photo', 'bio', 
            'sort_order', 'is_active'
        ]
        extra_kwargs = {
            'photo': {'required': False}
        }
