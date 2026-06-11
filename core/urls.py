from django.contrib import admin
from django.urls import path, include
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework_simplejwt.views import token_obtain_pair, token_refresh
from django.conf import settings
from django.conf.urls.static import static

schema_view = get_schema_view(
    openapi.Info(
        title="Academik Litsey API",
        default_version='v3',
        description="Test description",
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="contact@snippets.local"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('', include('main.urls', namespace='main')),
    path('', include('content.urls', namespace='content')),
    path('', include('structure.urls', namespace='structure')),
    path('', include('activities.urls', namespace='activities')),
    path('', include('admission.urls', namespace='admission')),
    path('', include('gallery.urls', namespace='gallery')),
    path('', include('contact.urls', namespace='contact')),
    path('', include('library.urls', namespace='library')),
]

urlpatterns += [
    path('', include('accounts.urls', namespace='accounts')),
    path('', include('settings_app.urls', namespace='settings_app')),
    path('token/refresh/', token_refresh),
]

# Media fayllar har doim serve qilinadi (production da Nginx orqali yoki whitenoise)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
