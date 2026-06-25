import logging
from io import BytesIO

from PIL import Image

logger = logging.getLogger(__name__)


def encode_image(image, quality=82):
    """Re-encode a PIL image into an optimized in-memory buffer."""
    img_format = (image.format or 'JPEG').upper()
    if img_format == 'JPEG' and image.mode in ('RGBA', 'P'):
        image = image.convert('RGB')
    buffer = BytesIO()
    save_kwargs = {'format': img_format, 'optimize': True}
    if img_format == 'JPEG':
        save_kwargs['quality'] = quality
    image.save(buffer, **save_kwargs)
    return buffer


def compress_image_field(field_file, max_width=1920, max_height=1920, quality=82):
    """Resize/recompress a freshly uploaded (uncommitted) image before it reaches storage."""
    from django.core.files.base import ContentFile

    if not field_file or getattr(field_file, '_committed', True):
        return  # empty, or an already-stored file — nothing new to compress

    try:
        image = Image.open(field_file)
        image.load()
    except Exception:
        logger.warning("Image compress: could not open %s", getattr(field_file, 'name', '?'))
        return

    if image.width > max_width or image.height > max_height:
        image.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)

    buffer = encode_image(image, quality)
    if buffer.tell() >= field_file.size:
        return  # already smaller than our re-encode — keep the original

    field_file.file = ContentFile(buffer.getvalue())
