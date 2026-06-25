from .image_utils import compress_image_field

# 'app_label.ModelName' -> {field_name: compress_image_field kwargs}
IMAGE_FIELDS = {
    'gallery.GalleryAlbum': {'cover_image': {}},
    'gallery.GalleryPhoto': {
        'image': {},
        'thumbnail': {'max_width': 600, 'max_height': 600, 'quality': 78},
    },
    'gallery.InfrastructureItem': {'image': {}},
    'gallery.Video': {'thumbnail': {'max_width': 800, 'max_height': 800}},
    'gallery.UsefulLink': {'logo': {'max_width': 512, 'max_height': 512, 'quality': 90}},
    'content.News': {'image': {}},
    'content.Announcement': {'image': {}},
    'settings_app.Slider': {'image': {'max_width': 2400, 'max_height': 2400, 'quality': 85}},
    'settings_app.SiteSettings': {'logo': {'max_width': 512, 'max_height': 512, 'quality': 90}},
    'library.LibraryResource': {'cover_image': {'max_width': 800, 'max_height': 1200, 'quality': 85}},
    'activities.Circle': {'photo': {}},
    'structure.Teacher': {'photo': {'max_width': 1000, 'max_height': 1000}},
    'structure.Management': {'photo': {'max_width': 1000, 'max_height': 1000}},
}


def compress_uploaded_images(sender, instance, **kwargs):
    label = f'{sender._meta.app_label}.{sender.__name__}'
    fields = IMAGE_FIELDS.get(label)
    if not fields:
        return
    for field_name, options in fields.items():
        compress_image_field(getattr(instance, field_name, None), **options)
