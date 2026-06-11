from django.urls import path
from .views import (
    LibraryStatsView,
    LibraryResourceListView,
    LibraryResourceDetailView,
)

app_name = 'library'

urlpatterns = [
    # Statistika (singleton)
    path('library/stats/', LibraryStatsView.as_view(), name='library-stats'),

    # Resurslar
    path('library/resources/', LibraryResourceListView.as_view(), name='library-resource-list'),
    path('library/resources/<int:pk>/', LibraryResourceDetailView.as_view(), name='library-resource-detail'),
]
