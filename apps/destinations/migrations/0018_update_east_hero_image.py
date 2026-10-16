from django.db import migrations


def update_east_hero_image(apps, schema_editor):
    Region = apps.get_model('destinations', 'Region')
    Region.objects.filter(slug='east', static_image='images/east/hero-east-sunset.jpg').update(
        static_image='images/east/hero-east-sunset.jpeg',
    )


class Migration(migrations.Migration):

    dependencies = [
        ('destinations', '0017_remove_seeded_east_place_descriptions'),
    ]

    operations = [
        migrations.RunPython(update_east_hero_image, migrations.RunPython.noop),
    ]
