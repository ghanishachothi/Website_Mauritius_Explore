import os

from django.db import migrations
from django.utils.text import slugify

# depends on the migration just before this one (found automatically)
_here = os.path.dirname(os.path.abspath(__file__))
_me = os.path.basename(__file__)[:4]
_prev = sorted(f[:-3] for f in os.listdir(_here)
               if f.endswith(".py") and f[:4].isdigit() and f[:4] < _me)[-1]

FOOD = [  # name, kind, location, rating, price, photo, description
    ("Gateau Piment", "cuisine", "Port Louis", "4.6", 7, "gateau-piment.png", "Crispy split-pea chilli fritters, the island's favourite street snack."),
    ("Halim", "cuisine", "Port Louis", "4.5", 150, "halim.png", "Spicy lentil and meat soup, served with lime and bread."),
    ("Mine Frite", "cuisine", "Port Louis", "4.6", 200, "mine-frite.png", "Stir-fried noodles with vegetables, chicken or shrimp."),
    ("Boulettes", "cuisine", "Port Louis", "4.7", 150, "boulettes.png", "Steamed dumplings in hot broth with chilli sauce."),
    ("Vindaye Poisson", "cuisine", "Mahebourg", "4.6", 350, "vindaye-poisson.png", "Fish in a tangy mustard, turmeric and garlic sauce."),
    ("Napolitaine", "cuisine", "Rose Hill", "4.5", 40, "napolitaine.png", "Sweet shortbread with jam and pink icing, perfect with tea."),
    ("Fried Rice", "cuisine", "Port Louis", "4.5", 200, "fried-rice.png", "Sino-Mauritian fried rice with egg and vegetables."),
    ("Octopus Curry", "cuisine", "Mahebourg", "4.7", 400, "octopus-curry.png", "Cari ourite: spicy octopus curry, a seaside favourite."),
    ("Bol Renverse", "cuisine", "Port Louis", "4.6", 250, "bol-renverse.png", "Upside-down bowl of rice, stir-fry and a fried egg."),
    ("Gateau Patate", "cuisine", "Curepipe", "4.4", 40, "gateau-patate.png", "Sweet potato and coconut turnovers."),
    ("Poutou", "cuisine", "Port Louis", "4.4", 40, "poutou.png", "Steamed rice cake with coconut, a sweet morning treat."),
    ("China Town Food Tour", "quest", "Port Louis", "4.8", 0, "china-town.png", "Walk Chinatown's lantern streets and taste dumplings, noodles and more."),
    ("Caudan Food Festival", "quest", "Caudan Waterfront", "4.7", 800, "food-festival-caudan.png", "Street food stalls, music and flavours at the Caudan festival."),
    ("Alouda Pillay", "quest", "Port Louis", "4.8", 100, "alouda-pillay.png", "The famous alouda at Pillay's in Port Louis market."),
]


def add_food(apps, schema_editor):
    FoodExperience = apps.get_model("experiences", "FoodExperience")
    for i, (name, kind, place, rating, price, photo, text) in enumerate(FOOD, start=10):
        FoodExperience.objects.update_or_create(slug=slugify(name), defaults=dict(
            name=name, kind=kind, location=place, rating=rating, price=price,
            static_image="images/food/" + photo, description=text, order=i))
    FoodExperience.objects.filter(slug="local-market-food-experience").update(price=0)


def remove_food(apps, schema_editor):
    FoodExperience = apps.get_model("experiences", "FoodExperience")
    FoodExperience.objects.filter(slug__in=[slugify(f[0]) for f in FOOD]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("experiences", _prev),
    ]

    operations = [
        migrations.RunPython(add_food, remove_food),
    ]

