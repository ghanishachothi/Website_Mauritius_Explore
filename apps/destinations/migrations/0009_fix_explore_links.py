from django.db import migrations


def fix_links(apps, schema_editor):
    Way = apps.get_model('destinations', 'WayToExplore')

    Way.objects.filter(title='Step Into History').update(
        url='/experiences/category/history/')

    Way.objects.filter(title__in=['Dive Into Nature', 'Culture', 'Rainbow Island']).update(
        title='Rainbow Island',
        text='Temples, mosques, churches & pagodas living side by side.',
        url='/experiences/category/culture/',
        static_image='images/explore/ways/culture.jpg',
        keywords='culture rainbow religion temple mosque church pagoda festival heritage')

    Way.objects.filter(title='Savour Local Flavours').update(
        url='/experiences/category/food/')
    Way.objects.filter(title='Hike & Explore').update(
        url='/experiences/category/nature/')
    Way.objects.filter(title='Live Like a Local').update(
        url='/experiences/category/local_experience/')


class Migration(migrations.Migration):
    dependencies = [('destinations', '0008_region_accent_color_region_card_color_and_more')]
    operations = [migrations.RunPython(fix_links, migrations.RunPython.noop)]