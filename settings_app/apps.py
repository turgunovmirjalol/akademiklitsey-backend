from django.apps import AppConfig


class SettingsAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'settings_app'
    verbose_name = 'Sozlamalar'

    def ready(self):
        from django.db.models.signals import post_migrate
        post_migrate.connect(create_default_settings, sender=self)


def create_default_settings(sender, **kwargs):
    """Seed a default SiteSettings row after migrations.

    Runs on post_migrate (not at import/startup) so it never queries a table
    that doesn't exist yet — which would crash `migrate`/`check` on a fresh DB.
    """
    from django.db import OperationalError, ProgrammingError
    from .models import SiteSettings
    try:
        if not SiteSettings.objects.exists():
            SiteSettings.objects.create(
                short_name_uz="Akademik Litsey",
                full_name_uz="Akademik Litsey",
                address_uz="Toshkent shahri",
                established_year=2000,
            )
    except (OperationalError, ProgrammingError):
        pass
