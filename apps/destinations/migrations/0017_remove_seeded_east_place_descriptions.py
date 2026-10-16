from django.db import migrations


SEEDED_DESCRIPTIONS = [
    'Sample description for Ile aux Cerfs.',
    'A stunning island getaway famous for its pristine beaches, water sports and crystal-clear lagoon.',
    'Take a boat to this beautiful island for powder-soft beaches, clear lagoon water and a full day of swimming and water activities.',
    'One of Mauritius’ most beautiful beaches, perfect for swimming, sunbathing and long walks by the sea.',
    'A breathtaking waterfall surrounded by tropical vegetation, accessible by boat for a unique adventure.',
    'A vibrant temple reflecting Mauritius’ rich cultural and spiritual heritage.',
    'A peaceful natural spot with many trails, popular for picnics, fishing and relaxing in nature.',
    'A peaceful natural spot, popular for picnics, fishing and relaxing in nature.',
    'A peaceful natural spot with many trails, popular for picnics, birdwatching and relaxing in nature.',
    'A charming village and lagoon known for boat trips to Île aux Cerfs and authentic local experiences.',
    'Enjoy the rhythms of traditional sega by the shore and experience the warmth of Mauritian music and dance.',
]


def clear_seeded_place_descriptions(apps, schema_editor):
    Destination = apps.get_model('destinations', 'Destination')
    Destination.objects.filter(
        region__slug='east',
        short_description__in=SEEDED_DESCRIPTIONS,
    ).update(short_description='')


class Migration(migrations.Migration):

    dependencies = [
        ('destinations', '0016_polish_east_island_description'),
    ]

    operations = [
        migrations.RunPython(clear_seeded_place_descriptions, migrations.RunPython.noop),
    ]
