from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.parsers import MultiPartParser, FormParser
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from accounts.permissions import IsAdminUser
from .models import News, Announcement, NewsImage, AnnouncementImage
from .serializers import (
    NewsListSerializer, NewsDetailSerializer, NewsWriteSerializer,
    AnnouncementListSerializer, AnnouncementDetailSerializer, AnnouncementWriteSerializer,
    NewsImageSerializer, AnnouncementImageSerializer, NewsImageUploadSerializer, AnnouncementImageUploadSerializer
)
from .pagination import CustomPagination


class BaseContentView(generics.GenericAPIView):
    """Content uchun asosiy view - umumiy funksiyalar"""
    pagination_class = CustomPagination
    filter_backends = [DjangoFilterBackend]
    
    def get_permissions(self):
        if self.request.method in ['GET']:
            return [AllowAny()]
        return [IsAdminUser()]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Faqat published statusdagi kontentni ko'rsatish (GET so'rovlari uchun)
        if self.request.method == 'GET':
            queryset = queryset.filter(status='published')
        
        # Search funksiyasi
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) | 
                Q(short_description__icontains=search)
            )
        
        return queryset


class NewsListView(BaseContentView):
    """Yangiliklar ro'yxati - GET, POST"""
    
    def get_serializer_class(self):
        if self.request.method == 'GET':
            return NewsListSerializer
        return NewsWriteSerializer
    
    queryset = News.objects.all()
    filterset_fields = ['status', 'is_featured']
    
    def get(self, request):
        """Yangiliklar ro'yxati - pagination bilan"""
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response({'success': True, 'data': serializer.data})
    
    def post(self, request):
        """Yangi yangilik qo'shish - faqat admin"""
        serializer = self.get_serializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            news = serializer.save()
            # Response uchun detail serializer ishlatish
            response_serializer = NewsDetailSerializer(news)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class NewsFeaturedView(BaseContentView):
    """Bosh sahifa uchun featured yangiliklar"""
    
    def get_serializer_class(self):
        return NewsListSerializer
    
    queryset = News.objects.filter(is_featured=True, status='published')
    pagination_class = None  # Limit qo'llanilgani uchun pagination kerak emas
    
    def get(self, request):
        """Featured yangiliklar (limit 3)"""
        news = self.get_queryset()[:3]
        serializer = self.get_serializer(news, many=True)
        return Response({'success': True, 'data': serializer.data})


class NewsDetailView(BaseContentView):
    """Bitta yangilik - GET, PUT, DELETE"""
    
    def get_serializer_class(self):
        if self.request.method == 'GET':
            return NewsDetailSerializer
        return NewsWriteSerializer
    
    queryset = News.objects.all()
    
    def get_object(self):
        """Slug orqali yangilikni olish"""
        return get_object_or_404(News, slug=self.kwargs['slug'])
    
    def get(self, request, slug):
        """Bitta yangilikni ko'rish"""
        news = self.get_object()
        # Faqat published yangilikni ko'rish mumkin
        if news.status != 'published':
            return Response(
                {'error': 'Bu yangilik hali nashr qilinmagan'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = self.get_serializer(news)
        return Response({'success': True, 'data': serializer.data})
    
    def put(self, request, slug):
        """Yangilikni yangilash - faqat admin"""
        news = self.get_object()
        serializer = self.get_serializer(news, data=request.data, context={'request': request})
        if serializer.is_valid():
            updated_news = serializer.save()
            response_serializer = NewsDetailSerializer(updated_news)
            return Response(response_serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, slug):
        """Yangilikni o'chirish - faqat admin"""
        news = self.get_object()
        news.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class NewsIncrementViewsView(generics.GenericAPIView):
    permission_classes = [AllowAny]
    queryset = News.objects.all()

    @swagger_auto_schema(auto_schema=None)
    def patch(self, request, slug):
        news = get_object_or_404(News, slug=slug)
        news.increment_views()

        return Response({
            'success': True,
            'views_count': news.views_count
        })


class AnnouncementListView(BaseContentView):
    """E'lonlar ro'yxati - GET, POST"""
    
    def get_serializer_class(self):
        if self.request.method == 'GET':
            return AnnouncementListSerializer
        return AnnouncementWriteSerializer
    
    queryset = Announcement.objects.all()
    filterset_fields = ['status', 'is_important']
    
    def get(self, request):
        """E'lonlar ro'yxati - pagination bilan"""
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response({'success': True, 'data': serializer.data})
    
    def post(self, request):
        """Yangi e'lon qo'shish - faqat admin"""
        serializer = self.get_serializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            announcement = serializer.save()
            response_serializer = AnnouncementDetailSerializer(announcement)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AnnouncementFeaturedView(BaseContentView):
    """Bosh sahifa uchun featured e'lonlar"""
    
    def get_serializer_class(self):
        return AnnouncementListSerializer
    
    queryset = Announcement.objects.filter(status='published').order_by('-is_important', '-published_at')
    pagination_class = None
    
    def get(self, request):
        """Featured e'lonlar (limit 3)"""
        announcements = self.get_queryset()[:3]
        serializer = self.get_serializer(announcements, many=True)
        return Response({'success': True, 'data': serializer.data})


class AnnouncementDetailView(BaseContentView):
    """Bitta e'lon - GET, PUT, DELETE"""
    
    def get_serializer_class(self):
        if self.request.method == 'GET':
            return AnnouncementDetailSerializer
        return AnnouncementWriteSerializer
    
    queryset = Announcement.objects.all()
    
    def get_object(self):
        return get_object_or_404(Announcement, slug=self.kwargs['slug'])
    
    def get(self, request, slug):
        """Bitta e'lonni ko'rish"""
        announcement = self.get_object()
        if announcement.status != 'published':
            return Response(
                {'error': 'Bu e\'lon hali nashr qilinmagan'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = self.get_serializer(announcement)
        return Response({'success': True, 'data': serializer.data})
    
    def put(self, request, slug):
        """E'lonni yangilash - faqat admin"""
        announcement = self.get_object()
        serializer = self.get_serializer(announcement, data=request.data, context={'request': request})
        if serializer.is_valid():
            updated_announcement = serializer.save()
            response_serializer = AnnouncementDetailSerializer(updated_announcement)
            return Response(response_serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, slug):
        """E'lonni o'chirish - faqat admin"""
        announcement = self.get_object()
        announcement.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class NewsImageView(generics.GenericAPIView):
    """Yangilik rasmlari uchun view - faqat adminlar"""
    permission_classes = [IsAdminUser]
    serializer_class = NewsImageSerializer
    queryset = NewsImage.objects.all()
    
    def get_object(self):
        return get_object_or_404(NewsImage, pk=self.kwargs['pk'], news__slug=self.kwargs['slug'])
    
    def delete(self, request, slug, pk):
        """Rasmani o'chirish - faqat admin"""
        image = self.get_object()
        image.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class AnnouncementImageView(generics.GenericAPIView):
    """E'lon rasmlari uchun view - faqat adminlar"""

    permission_classes = [IsAdminUser]
    serializer_class = AnnouncementImageSerializer
    queryset = AnnouncementImage.objects.all()  # ← SHU QATORNI QO‘SHING

    def get_object(self):
        return get_object_or_404(
            AnnouncementImage,
            pk=self.kwargs['pk'],
            announcement__slug=self.kwargs['slug']
        )

    @swagger_auto_schema(auto_schema=None)  # Swaggerda ko'rinmasligi uchun
    def delete(self, request, slug, pk):
        """Rasmani o'chirish - faqat admin"""
        image = self.get_object()
        image.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class NewsImageUploadView(generics.GenericAPIView):
    """Yangilikka rasm yuklash - faqat adminlar"""
    permission_classes = [IsAdminUser]
    parser_classes = [MultiPartParser, FormParser]
    serializer_class = NewsImageUploadSerializer
    
    @swagger_auto_schema(
        operation_description="Yangilikka rasm yuklash",
        manual_parameters=[
            openapi.Parameter(
                'image',
                openapi.IN_FORM,
                description="Rasm fayli",
                type=openapi.TYPE_FILE,
                required=True
            ),
            openapi.Parameter(
                'caption',
                openapi.IN_FORM,
                description="Rasm izohi",
                type=openapi.TYPE_STRING,
                required=False
            ),
            openapi.Parameter(
                'sort_order',
                openapi.IN_FORM,
                description="Tartib raqami",
                type=openapi.TYPE_INTEGER,
                required=False
            ),
        ],
        responses={201: NewsImageSerializer}
    )
    def post(self, request, slug):
        """Yangilikka yangi rasm yuklash"""
        news = get_object_or_404(News, slug=slug)
        
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save(news=news)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AnnouncementImageUploadView(generics.GenericAPIView):
    """E'longa rasm yuklash - faqat adminlar"""
    permission_classes = [IsAdminUser]
    parser_classes = [MultiPartParser, FormParser]
    serializer_class = AnnouncementImageUploadSerializer
    
    @swagger_auto_schema(
        operation_description="E'longa rasm yuklash",
        manual_parameters=[
            openapi.Parameter(
                'image',
                openapi.IN_FORM,
                description="Rasm fayli",
                type=openapi.TYPE_FILE,
                required=True
            ),
            openapi.Parameter(
                'caption',
                openapi.IN_FORM,
                description="Rasm izohi",
                type=openapi.TYPE_STRING,
                required=False
            ),
            openapi.Parameter(
                'sort_order',
                openapi.IN_FORM,
                description="Tartib raqami",
                type=openapi.TYPE_INTEGER,
                required=False
            ),
        ],
        responses={201: AnnouncementImageSerializer}
    )
    def post(self, request, slug):
        """E'longa yangi rasm yuklash"""
        announcement = get_object_or_404(Announcement, slug=slug)
        
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save(announcement=announcement)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
