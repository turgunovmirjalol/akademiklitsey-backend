from django.apps import AppConfig


class SettingsAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'settings_app'
    verbose_name = 'Sozlamalar'

    def ready(self):
        from .models import SiteSettings
        if not SiteSettings.objects.exists():
            SiteSettings.objects.create(
                short_name_uz="Akademik Litsey",
                full_name_uz="Akademik Litsey",
                address_uz="Toshkent shahri",
                established_year=2000,
            )
