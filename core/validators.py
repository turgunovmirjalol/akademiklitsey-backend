"""
Fayl yuklash uchun umumiy validatorlar.
Barcha app larda ishlatiladi.
"""
import os
from rest_framework import serializers

# ─── Rasm validatsiyasi ───────────────────────────────────────────────────────
IMAGE_MAX_SIZE = 8 * 1024 * 1024  # 8 MB
IMAGE_ALLOWED_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.webp', '.gif']
IMAGE_ALLOWED_CONTENT_TYPES = [
    'image/jpeg', 'image/png', 'image/webp', 'image/gif'
]

# ─── Video validatsiyasi ──────────────────────────────────────────────────────
VIDEO_MAX_SIZE = 500 * 1024 * 1024  # 500 MB
VIDEO_ALLOWED_EXTENSIONS = ['.mp4', '.webm', '.avi', '.mov', '.mpeg', '.mpg']
VIDEO_ALLOWED_CONTENT_TYPES = [
    'video/mp4', 'video/webm', 'video/avi',
    'video/quicktime', 'video/x-msvideo', 'video/mpeg'
]

# ─── Hujjat validatsiyasi ─────────────────────────────────────────────────────
DOCUMENT_MAX_SIZE = 30 * 1024 * 1024  # 30 MB
DOCUMENT_ALLOWED_EXTENSIONS = ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.pptx', '.txt']
DOCUMENT_ALLOWED_CONTENT_TYPES = [
    'application/pdf',
    'application/msword',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'application/vnd.ms-excel',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    'application/vnd.openxmlformats-officedocument.presentationml.presentation',
    'text/plain',
]


def validate_image(value):
    """Rasm faylini tekshiradi: hajm va format."""
    if value is None:
        return value

    if value.size > IMAGE_MAX_SIZE:
        size_mb = round(value.size / (1024 * 1024), 2)
        raise serializers.ValidationError(
            f"Rasm hajmi juda katta: {size_mb} MB. Maksimal: 8 MB."
        )

    ext = os.path.splitext(value.name)[1].lower()
    if ext not in IMAGE_ALLOWED_EXTENSIONS:
        raise serializers.ValidationError(
            f"Noto'g'ri format: '{ext}'. Ruxsat etilganlar: jpg, jpeg, png, webp, gif."
        )

    content_type = getattr(value, 'content_type', '')
    if content_type and content_type not in IMAGE_ALLOWED_CONTENT_TYPES:
        raise serializers.ValidationError(
            f"Noto'g'ri fayl turi: '{content_type}'. Faqat rasm fayllar qabul qilinadi."
        )

    return value


def validate_video(value):
    """Video faylini tekshiradi: hajm va format."""
    if value is None:
        return value

    if value.size > VIDEO_MAX_SIZE:
        size_mb = value.size // (1024 * 1024)
        raise serializers.ValidationError(
            f"Video hajmi juda katta: {size_mb} MB. Maksimal: 500 MB."
        )

    ext = os.path.splitext(value.name)[1].lower()
    if ext not in VIDEO_ALLOWED_EXTENSIONS:
        raise serializers.ValidationError(
            f"Noto'g'ri format: '{ext}'. Ruxsat etilganlar: mp4, webm, avi, mov."
        )

    content_type = getattr(value, 'content_type', '')
    if content_type and content_type not in VIDEO_ALLOWED_CONTENT_TYPES:
        raise serializers.ValidationError(
            f"Noto'g'ri fayl turi: '{content_type}'. Faqat video fayllar qabul qilinadi."
        )

    return value


def validate_document(value):
    """Hujjat faylini tekshiradi: hajm va format."""
    if value is None:
        return value

    if value.size > DOCUMENT_MAX_SIZE:
        size_mb = round(value.size / (1024 * 1024), 2)
        raise serializers.ValidationError(
            f"Fayl hajmi juda katta: {size_mb} MB. Maksimal: 30 MB."
        )

    ext = os.path.splitext(value.name)[1].lower()
    if ext not in DOCUMENT_ALLOWED_EXTENSIONS:
        raise serializers.ValidationError(
            f"Noto'g'ri format: '{ext}'. Ruxsat etilganlar: pdf, doc, docx, xls, xlsx, pptx, txt."
        )

    return value
