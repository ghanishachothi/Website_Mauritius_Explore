"""Taste Mauritius: starter food cards + "Savour Local Flavours" opens the food frame."""
from django.db import migrations
from django.utils.text import slugify

FOOD = [  # name, kind, location, rating, price
    ("Mine bouille", "cuisine", "Pamplemousses", "4.8", 400),
    ("Traditional 7 Cari", "cuisine", "Pamplemousses", "4.5", 350),
    ("Mauritian Biryani", "cuisine", "Vacoas", "4.7", 350),
    ("Mauritian Tea", "cuisine", "Port Louis", "4.5", 100),
    ("Local Market Food Experience", "quest", "Mahebourg Bay", "4.7", 1500),
]


def add_food(apps, schema_editor):
    FoodExperience = apps.get_model("experiences", "FoodExperience")
    for i, (name, kind, place, rating, price) in enumerate(FOOD):
        FoodExperience.objects.get_or_create(name=name, defaults=dict(
            slug=slugify(name), kind=kind, location=place, rating=rating, price=price, order=i))
    WayToExplore = apps.get_model("destinations", "WayToExplore")
    WayToExplore.objects.filter(title="Savour Local Flavours").update(url="/experiences/food/")


class Migration(migrations.Migration):

    dependencies = [
        ('experiences', '0002_foodexperience'),
        ('destinations', '0004_explore_content'),
    ]

    operations = [
        migrations.RunPython(add_food, migrations.RunPython.noop),
    ]
