from django.db import migrations


EAST_HIGHLIGHTS = [
    ('fa-solid fa-umbrella-beach', 'Stunning Beaches'),
    ('fa-solid fa-water', 'Water Activities'),
    ('fa-solid fa-mountain-sun', 'Waterfalls & Rivers'),
    ('fa-solid fa-spa', 'Spiritual Sites'),
    ('fa-solid fa-landmark', 'Cultural Heritage'),
    ('fa-solid fa-house', 'Local Villages'),
    ('fa-solid fa-leaf', 'Lush Greenery'),
    ('fa-solid fa-camera', 'Scenic Viewpoints'),
]

def populate_east_region(apps, schema_editor):
    Region = apps.get_model('destinations', 'Region')
    RegionHighlight = apps.get_model('destinations', 'RegionHighlight')
    region = Region.objects.filter(slug='east').first()
    if region is None:
        return

    defaults = {
        'tagline': ('Charming villages, beaches and lagoon escapes.',
                    'Where the ocean meets authentic charm'),
        'about_text': ('', 'The East is a blend of natural beauty, cultural heritage and tranquil villages. '
                           'From idyllic islands and waterfalls to historic temples and lush landscapes, '
                           'it offers a slower pace of life and authentic Mauritian experiences.'),
        'travel_tip': ('', 'The best time to explore the East is from May to December for pleasant weather '
                           'and calmer seas.\n\nDon’t forget your sunscreen, light clothing and a camera '
                           'to capture the stunning scenery and memories!'),
        'description': ('', 'The East of Mauritius is a paradise of turquoise lagoons, powdery beaches, '
                            'lush greenery and vibrant culture — offering the perfect escape for '
                            'relaxation, adventure and unforgettable memories.'),
    }
    for field, (old_default, new_default) in defaults.items():
        current = getattr(region, field)
        if not current or current == old_default:
            setattr(region, field, new_default)

    if not region.static_image or region.static_image == 'images/explore/regions/east.jpg':
        region.static_image = 'images/east/hero-east-sunset.jpeg'

    for field, old_default, new_default in (
        ('theme_color', '#2b1d10', '#f3f6fb'),
        ('card_color', '#24170c', '#08234e'),
        ('accent_color', '#f0a63a', '#32c9e8'),
    ):
        if getattr(region, field) == old_default:
            setattr(region, field, new_default)
    region.save()

    if not RegionHighlight.objects.filter(region=region).exists():
        RegionHighlight.objects.bulk_create([
            RegionHighlight(region=region, icon=icon, label=label, order=order)
            for order, (icon, label) in enumerate(EAST_HIGHLIGHTS)
        ])


class Migration(migrations.Migration):

    dependencies = [
        ('destinations', '0012_region_hero_dark_text_region_hero_gradient'),
    ]

    operations = [
        migrations.RunPython(populate_east_region, migrations.RunPython.noop),
    ]
