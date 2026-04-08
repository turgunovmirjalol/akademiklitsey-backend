from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.parsers import MultiPartParser, FormParser
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q
from accounts.permissions import IsAdminUser
from content.pagination import CustomPagination
from .models import Department, Teacher, Management
from .serializers import (
    DepartmentSerializer, DepartmentDetailSerializer, DepartmentWriteSerializer,
    TeacherListSerializer, TeacherDetailSerializer, TeacherWriteSerializer,
    ManagementSerializer, ManagementWriteSerializer
)


class BaseStructureView(generics.GenericAPIView):
    """Structure uchun asosiy view - umumiy funksiyalar"""
    pagination_class = CustomPagination
    filter_backends = [DjangoFilterBackend]
    
    def get_permissions(self):
        if self.request.method in ['GET']:
            return [AllowAny()]
        return [IsAdminUser()]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Faqat active obyektlarni ko'rsatish (GET so'rovlari uchun)
        if self.request.method == 'GET':
            queryset = queryset.filter(is_active=True)
        
        # Search funksiyasi
        search = self.request.query_params.get('search', None)
        if search:
            if hasattr(queryset.model, 'full_name'):
                queryset = queryset.filter(full_name__icontains=search)
            elif hasattr(queryset.model, 'name'):
                queryset = queryset.filter(name__icontains=search)
        
        return queryset


class DepartmentListView(BaseStructureView):
    """Kafedralar ro'yxati - GET, POST"""
    
    def get_serializer_class(self):
        if self.request.method == 'GET':
            return DepartmentSerializer
        return DepartmentWriteSerializer
    
    queryset = Department.objects.all()
    filterset_fields = ['is_active']
    
    def get(self, request):
        """Kafedralar ro'yxati - pagination bilan"""
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response({'success': True, 'data': serializer.data})
    
    def post(self, request):
        """Yangi kafedra qo'shish - faqat admin"""
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            department = serializer.save()
            response_serializer = DepartmentSerializer(department)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DepartmentDetailView(BaseStructureView):
    """Bitta kafedra - GET, PUT, DELETE"""
    
    def get_serializer_class(self):
        if self.request.method == 'GET':
            return DepartmentDetailSerializer
        return DepartmentWriteSerializer
    
    queryset = Department.objects.all()
    
    def get_object(self):
        return get_object_or_404(Department, slug=self.kwargs['slug'])
    
    def get(self, request, slug):
        """Bitta kafedra ma'lumotlari (o'qituvchilar bilan)"""
        department = self.get_object()
        serializer = self.get_serializer(department)
        return Response({'success': True, 'data': serializer.data})
    
    def put(self, request, slug):
        """Kafedrani yangilash - faqat admin"""
        department = self.get_object()
        serializer = self.get_serializer(department, data=request.data)
        if serializer.is_valid():
            updated_department = serializer.save()
            response_serializer = DepartmentDetailSerializer(updated_department)
            return Response(response_serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, slug):
        """Kafedrani o'chirish - faqat admin"""
        department = self.get_object()
        department.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class TeacherListView(BaseStructureView):
    """O'qituvchilar ro'yxati - GET, POST"""
    
    def get_serializer_class(self):
        if self.request.method == 'GET':
            return TeacherListSerializer
        return TeacherWriteSerializer
    
    queryset = Teacher.objects.all()
    filterset_fields = ['department', 'category', 'is_active']
    parser_classes = [MultiPartParser, FormParser]
    
    def get(self, request):
        """O'qituvchilar ro'yxati - pagination va filter bilan"""
        queryset = self.filter_queryset(self.get_queryset())
        
        # Kafedra bo'yicha filter
        department_id = request.query_params.get('department_id', None)
        if department_id:
            queryset = queryset.filter(department_id=department_id)
        
        # Category bo'yicha filter
        category = request.query_params.get('category', None)
        if category:
            queryset = queryset.filter(category=category)
        
        page = self.paginate_queryset(queryset)
        
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response({'success': True, 'data': serializer.data})
    
    def post(self, request):
        """Yangi o'qituvchi qo'shish - faqat admin"""
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            teacher = serializer.save()
            response_serializer = TeacherDetailSerializer(teacher)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class TeacherDetailView(BaseStructureView):
    """Bitta o'qituvchi - GET, PUT, DELETE"""
    
    def get_serializer_class(self):
        if self.request.method == 'GET':
            return TeacherDetailSerializer
        return TeacherWriteSerializer
    
    queryset = Teacher.objects.all()
    parser_classes = [MultiPartParser, FormParser]
    
    def get_object(self):
        return get_object_or_404(Teacher, slug=self.kwargs['slug'])
    
    def get(self, request, slug):
        """Bitta o'qituvchi ma'lumotlari"""
        teacher = self.get_object()
        serializer = self.get_serializer(teacher)
        return Response({'success': True, 'data': serializer.data})
    
    def put(self, request, slug):
        """O'qituvchini yangilash - faqat admin"""
        teacher = self.get_object()
        serializer = self.get_serializer(teacher, data=request.data)
        if serializer.is_valid():
            updated_teacher = serializer.save()
            response_serializer = TeacherDetailSerializer(updated_teacher)
            return Response(response_serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, slug):
        """O'qituvchini o'chirish - faqat admin"""
        teacher = self.get_object()
        teacher.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class TeacherByDepartmentView(BaseStructureView):
    """Kafedra bo'yicha o'qituvchilar"""
    
    def get_serializer_class(self):
        return TeacherListSerializer
    
    queryset = Teacher.objects.all()
    pagination_class = None  # Kafedra bo'yicha cheksiz ro'yxat
    
    def get(self, request, department_id):
        """Kafedra bo'yicha faol o'qituvchilar ro'yxati"""
        teachers = self.get_queryset().filter(
            department_id=department_id, 
            is_active=True
        ).order_by('sort_order', 'full_name')
        
        serializer = self.get_serializer(teachers, many=True)
        return Response({'success': True, 'data': serializer.data})


class ManagementListView(BaseStructureView):
    """Rahbariyat ro'yxati - GET, POST"""
    
    def get_serializer_class(self):
        if self.request.method == 'GET':
            return ManagementSerializer
        return ManagementWriteSerializer
    
    queryset = Management.objects.all()
    pagination_class = None  # Rahbariyat ko'p bo'lmaydi, pagination kerak emas
    parser_classes = [MultiPartParser, FormParser]
    
    def get(self, request):
        """Rahbariyat ro'yxati"""
        management = self.get_queryset().order_by('sort_order')
        serializer = self.get_serializer(management, many=True)
        return Response({'success': True, 'data': serializer.data})
    
    def post(self, request):
        """Yangi rahbar qo'shish - faqat admin"""
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            manager = serializer.save()
            response_serializer = ManagementSerializer(manager)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ManagementDetailView(BaseStructureView):
    """Bitta rahbar - GET, PUT, DELETE"""
    
    def get_serializer_class(self):
        if self.request.method == 'GET':
            return ManagementSerializer
        return ManagementWriteSerializer
    
    queryset = Management.objects.all()
    parser_classes = [MultiPartParser, FormParser]
    
    def get_object(self):
        return get_object_or_404(Management, pk=self.kwargs['pk'])
    
    def get(self, request, pk):
        """Bitta rahbar ma'lumotlari"""
        manager = self.get_object()
        serializer = self.get_serializer(manager)
        return Response({'success': True, 'data': serializer.data})
    
    def put(self, request, pk):
        """Rahberni yangilash - faqat admin"""
        manager = self.get_object()
        serializer = self.get_serializer(manager, data=request.data)
        if serializer.is_valid():
            updated_manager = serializer.save()
            response_serializer = ManagementSerializer(updated_manager)
            return Response(response_serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, pk):
        """Rahberni o'chirish - faqat admin"""
        manager = self.get_object()
        manager.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
