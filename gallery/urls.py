from django.urls import path
from .views import (
    GalleryAlbumListView,
    GalleryAlbumDetailView,
    GalleryPhotoUploadView,
    GalleryPhotoBulkUploadView,
    GalleryPhotoDetailView,
    UsefulLinkListView,
    UsefulLinkDetailView,
)

app_name = 'gallery'

urlpatterns = [
    # ─── Albums ──────────────────────────────────────────────────────────────
    # GET  — albomlar ro'yxati (filter, search, pagination)
    # POST — yangi album yaratish (admin)
    path('gallery/albums/', GalleryAlbumListView.as_view(), name='gallery-album-list'),

    # GET    — bitta album (rasmlar bilan)
    # PUT    — to'liq yangilash (admin)
    # PATCH  — qisman yangilash (admin)
    # DELETE — o'chirish (admin)
    path('gallery/albums/<slug:slug>/', GalleryAlbumDetailView.as_view(), name='gallery-album-detail'),

    # ─── Photos ──────────────────────────────────────────────────────────────
    # POST — albomga bitta rasm yuklash (admin)
    path('gallery/albums/<slug:slug>/photos/', GalleryPhotoUploadView.as_view(), name='gallery-photo-upload'),

    # POST — albomga bir nechta rasm yuklash (admin)
    path('gallery/albums/<slug:slug>/photos/bulk/', GalleryPhotoBulkUploadView.as_view(), name='gallery-photo-bulk'),

    # GET    — bitta rasm detali
    # PATCH  — rasmni yangilash (admin)
    # DELETE — rasmni o'chirish (admin)
    path('gallery/photos/<int:pk>/', GalleryPhotoDetailView.as_view(), name='gallery-photo-detail'),

    # ─── Useful Links ─────────────────────────────────────────────────────────
    # GET  — havolalar ro'yxati
    # POST — yangi havola (admin)
    path('useful-links/', UsefulLinkListView.as_view(), name='useful-link-list'),

    # GET    — bitta havola
    # PUT    — to'liq yangilash (admin)
    # PATCH  — qisman yangilash (admin)
    # DELETE — o'chirish (admin)
    path('useful-links/<int:pk>/', UsefulLinkDetailView.as_view(), name='useful-link-detail'),
]
