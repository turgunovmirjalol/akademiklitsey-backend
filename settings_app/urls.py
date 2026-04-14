from django.urls import path
from .views import SiteSettingsAPIView, SliderListCreateAPIView, SliderDetailAPIView

app_name = 'settings_app'

urlpatterns = [
    path('settings/', SiteSettingsAPIView.as_view(), name='site-settings'),
    path('sliders/', SliderListCreateAPIView.as_view(), name='slider-list'),
    path('sliders/<int:pk>/', SliderDetailAPIView.as_view(), name='slider-detail'),
]
