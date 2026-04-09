from django.urls import path
from .views import SiteSettingsAPIView

app_name = 'settings_app'

urlpatterns = [
    path('settings/', SiteSettingsAPIView.as_view(), name='site-settings'),
]
