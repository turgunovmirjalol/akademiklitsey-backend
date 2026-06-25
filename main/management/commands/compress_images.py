from django.apps import apps
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from PIL import Image

from main.image_signals import IMAGE_FIELDS
from main.image_utils import encode_image


def compress_existing(field_file, max_width=1920, max_height=1920, quality=82):
    """Resize/recompress an already-stored image in place. Returns (before, after) sizes or None."""
    if not field_file or not field_file.name:
        return None
    try:
        before = field_file.size
        field_file.open('rb')
        image = Image.open(field_file)
        image.load()
    except Exception:
        return None
    finally:
        field_file.close()

    if image.width > max_width or image.height > max_height:
        image.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)

    buffer = encode_image(image, quality)
    if buffer.tell() >= before:
        return None

    name = field_file.name
    field_file.delete(save=False)
    field_file.save(name, ContentFile(buffer.getvalue()), save=False)
    return before, field_file.size


class Command(BaseCommand):
    help = "Resize and recompress every already-uploaded image to cut page load weight."

    def handle(self, *args, **options):
        total_before = 0
        total_after = 0
        touched = 0

        for label, fields in IMAGE_FIELDS.items():
            app_label, model_name = label.split('.')
            model = apps.get_model(app_label, model_name)
            for instance in model.objects.all():
                changed = False
                for field_name, opts in fields.items():
                    field_file = getattr(instance, field_name, None)
                    result = compress_existing(field_file, **opts)
                    if result:
                        before, after = result
                        total_before += before
                        total_after += after
                        changed = True
                        self.stdout.write(
                            f"{label}#{instance.pk}.{field_name}: "
                            f"{before / 1024:.0f}KB -> {after / 1024:.0f}KB"
                        )
                if changed:
                    instance.save()
                    touched += 1

        saved_mb = (total_before - total_after) / (1024 * 1024)
        self.stdout.write(self.style.SUCCESS(
            f"Tayyor. {touched} ta obyekt yangilandi, jami {saved_mb:.1f} MB tejaldi."
        ))
