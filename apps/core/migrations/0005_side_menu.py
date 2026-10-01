"""Side menu "Explore the site": every frame. Everyone gets it with: python manage.py migrate"""
from django.db import migrations

MENU = [  # name, url, icon
    ("Discover Mauritius", "/", "home"),
    ("Explore the Island", "/destinations/", "map"),
    ("Explore Your Way", "/experiences/", "route"),
    ("Experience Insight", "/experiences/", "compass"),
    ("Guides & Packages", "/destinations/guides-packages/", "book"),
    ("Island Calendar", "/experiences/calendar/", "calendar"),
    ("Explore Board", "/destinations/board/", "board"),
    ("Reserve Your Experience", "/experiences/", "ticket"),
    ("Checkout", "/bookings/checkout/", "lock"),
    ("Explore Admin", "/dashboard/", "gear"),
]


def add_menu(apps, schema_editor):
    SitePage = apps.get_model("core", "SitePage")
    SitePage.objects.filter(location="side", name="My Experiences").delete()
    for i, (name, url, icon) in enumerate(MENU):
        SitePage.objects.update_or_create(name=name, location="menu", defaults=dict(
            url=url, icon=icon, order=i, header_line1=name, header_line2="", frame_ready=False))


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0004_alter_sitepage_icon_alter_sitepage_location'),
    ]

    operations = [
        migrations.RunPython(add_menu, migrations.RunPython.noop),
    ]
