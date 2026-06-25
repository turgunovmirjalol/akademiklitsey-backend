from django.apps import AppConfig


class MainConfig(AppConfig):
    name = 'main'

    def ready(self):
        from django.db.models.signals import pre_save

        from .image_signals import compress_uploaded_images

        pre_save.connect(compress_uploaded_images)
