from django.urls import path
from .views import (
    NewsListCreateAPIView,
    NewsDetailAPIView,
    AnnouncementListCreateAPIView,
    AnnouncementDetailAPIView,
)

app_name = 'content'

urlpatterns = [
    # ─── News CRUD ───────────────────────────────────────────
    # GET  – barcha yangiliklar (filter, search, pagination)
    # POST – yangi yangilik yaratish
    path('news/', NewsListCreateAPIView.as_view(), name='news-list-create'),

    # GET    – bitta yangilik (slug orqali)
    # PUT    – to'liq yangilash
    # PATCH  – qisman yangilash
    # DELETE – o'chirish
    path('news/<slug:slug>/', NewsDetailAPIView.as_view(), name='news-detail'),

    # ─── Announcements CRUD ───────────────────────────────────
    # GET  – barcha e'lonlar (filter, search, pagination)
    # POST – yangi e'lon yaratish
    path('announcements/', AnnouncementListCreateAPIView.as_view(), name='announcement-list-create'),

    # GET    – bitta e'lon (slug orqali)
    # PUT    – to'liq yangilash
    # PATCH  – qisman yangilash
    # DELETE – o'chirish
    path('announcements/<slug:slug>/', AnnouncementDetailAPIView.as_view(), name='announcement-detail'),
]