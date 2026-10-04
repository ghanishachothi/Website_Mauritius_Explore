"""
Explore the Island content: hero captions, ways to explore, regions and their places.
Everyone gets exactly this when they run: python manage.py migrate
Places that already exist (e.g. from the homepage) are kept and only get their note/keywords/region.
"""
from django.db import migrations
from django.utils.text import slugify

HERO_TILES = [  # tag, text, colour
    ("HERITAGE", "Timeless traditions and rich culture", "heritage"),
    ("LOCAL LIFE", "Markets, street food and everyday life", "local"),
    ("ADVENTURE", "Hike, trek and seek new perspectives", "adventure"),
    ("NATURAL BEAUTY", "Breathtaking places around every corner", "beauty"),
]

WAYS = [  # title, text, url, static image, keywords
    ("Step Into History", "Museums, colonial sites, temples & landmarks.", "/experiences/?category=culture",
     "images/explore/ways/step-into-history.jpg", "history heritage museum temple colonial culture landmark"),
    ("Dive Into Nature", "Waterfalls, nature parks, ocean life & more.", "/experiences/?category=water-sports",
     "images/explore/ways/dive-into-nature.jpg", "nature dive snorkel snorkelling ocean waterfall park turtle"),
    ("Savour Local Flavours", "Street food, markets, seafood & multi-cultural cuisine.", "/experiences/?category=food",
     "images/explore/ways/savour-local-flavours.jpg", "food eat street food dholl puri seafood cuisine restaurant"),
    ("Hike & Explore", "Trails, national parks, and breathtaking views.", "/experiences/?category=hiking",
     "images/explore/ways/hike-and-explore.jpg", "hike hiking trail trek walk mountain national park views"),
    ("Live Like a Local", "Markets, villages, artisans & traditions.", "/destinations/board/",
     "images/explore/ways/live-like-a-local.jpg", "local life village market artisan craft tradition"),
]

REGIONS = [  # name, list title, blurb, static image, scrim, wide, keywords
    ("North", "🌍 North Mauritius", "Lively towns, beaches and cultural spots.",
     "images/explore/regions/north.jpg", "light", False, "north grand baie pamplemousses"),
    ("South", "🌍 South Mauritius", "Wild landscapes, heritage sites and scenic beauty.",
     "images/explore/regions/south.jpg", "light", False, "south le morne chamarel"),
    ("East", "🌍 East Mauritius", "Charming villages, beaches and lagoon escapes.",
     "images/explore/regions/east.jpg", "light", False, "east belle mare flacq lagoon"),
    ("West", "🌍 West Mauritius", "Sunset views, beaches and adventure experiences.",
     "images/explore/regions/west.jpg", "dark", False, "west tamarin flic en flac sunset"),
    ("Central", "🌍 Central Mauritius", "Green heart of the island, rivers, parks and local life.",
     "images/explore/regions/central.jpg", "wide", True, "central curepipe plateau"),
]

PLACES = {  # region: [(name, note, keywords)]
    "North": [
        ("Pamplemousses Garden", "", "botanical garden water lilies sir seewoosagur ramgoolam"),
        ("Notre-Dame Auxiliatrice", "", "church red roof cap malheureux chapel"),
        ("Cap Malheureux", "fishing village", "village fishing church"),
        ("Fort Adelaide", "", "citadel fort port louis history"),
        ("Local Markets", "", "market shopping port louis bazaar"),
        ("Coin de Mire", "", "island gunner's quoin boat snorkelling"),
    ],
    "East": [
        ("Île aux Cerfs", "", "ile aux cerfs island boat golf beach"),
        ("Belle Mare", "", "beach swim lagoon"),
        ("GRSE Waterfall", "", "grand river south east waterfall boat"),
        ("Poste de Flacq Temple", "", "temple sagar shiv mandir"),
        ("Bras d'Eau", "", "national park forest walk"),
        ("Trou d'Eau Douce Lagoon", "village + lagoon", "lagoon village boat"),
    ],
    "Central": [
        ("Pieter Both", "", "mountain hike peak"),
        ("Eau Bouillie", "Nouvelle Découverte", "spring village nouvelle decouverte"),
        ("State House", "Réduit", "reduit history house"),
        ("Minissy Waterfall", "", "waterfall swim"),
        ("Trou aux Cerfs", "", "crater volcano curepipe viewpoint"),
        ("Quatre Bornes Market", "", "market shopping clothes"),
    ],
    "West": [
        ("Dolphins in Tamarin", "", "dolphin swim boat tamarin"),
        ("Black River Gorges Viewpoint", "", "national park viewpoint hike"),
        ("Martello Tower Museum", "", "museum history tower la preneuse"),
        ("Tamarin Fishing Village", "", "fishing village tamarin"),
        ("Casela Nature Parks", "", "casela lion zoo safari zipline"),
        ("Sunset at Flic en Flac", "", "sunset beach flic en flac"),
    ],
    "South": [
        ("Grand Bassin", "Ganga Talao", "lake temple shiva pilgrimage"),
        ("La Vanille Nature Park", "", "crocodile tortoise park"),
        ("Le Morne Brabant", "", "mountain hike unesco"),
        ("Seven Coloured Earths", "", "chamarel coloured earth geopark"),
        ("Frederica Nature Reserve", "", "reserve quad safari bel ombre"),
        ("Gris Gris Beach", "", "beach cliff souillac"),
    ],
}

# same place, other name already used on the homepage -> keep the homepage name
ALIASES = {
    "Pamplemousses Garden": ["Botanical Garden"],
    "Île aux Cerfs": ["Ile aux Cerfs"],
    "Belle Mare": ["Belle Mare Beach"],
    "Le Morne Brabant": ["Le Morne"],
    "Seven Coloured Earths": ["Seven Coloured Earth"],
    "Gris Gris Beach": ["Gris Gris"],
}


def add_explore_content(apps, schema_editor):
    HeroTile = apps.get_model("destinations", "HeroTile")
    WayToExplore = apps.get_model("destinations", "WayToExplore")
    Region = apps.get_model("destinations", "Region")
    Destination = apps.get_model("destinations", "Destination")

    for i, (tag, text, color) in enumerate(HERO_TILES):
        HeroTile.objects.update_or_create(tag=tag, defaults={"text": text, "color": color, "order": i})

    for i, (title, text, url, image, keys) in enumerate(WAYS):
        way, created = WayToExplore.objects.get_or_create(title=title, defaults={
            "text": text, "url": url, "static_image": image, "keywords": keys, "order": i})
        if not created and not way.static_image:
            way.static_image = image
            way.save()

    regions = {}
    for i, (name, list_title, blurb, image, scrim, wide, keys) in enumerate(REGIONS):
        region, _ = Region.objects.get_or_create(name=name, defaults={"slug": slugify(name)})
        region.list_title, region.tagline, region.static_image = list_title, blurb, image
        region.scrim, region.is_wide, region.keywords, region.order = scrim, wide, keys, i
        region.save()
        regions[name] = region

    for region_name, places in PLACES.items():
        for name, note, keys in places:
            place = Destination.objects.filter(name__in=[name] + ALIASES.get(name, [])).first()
            if place is None:
                slug, n = slugify(name), 2
                while Destination.objects.filter(slug=slug).exists():
                    slug, n = f"{slugify(name)}-{n}", n + 1
                place = Destination(name=name, slug=slug)
            place.region = regions[region_name]
            if note and not place.note:
                place.note = note
            if not place.keywords:
                place.keywords = keys
            place.save()


class Migration(migrations.Migration):

    dependencies = [
        ('destinations', '0003_herotile_waytoexplore_destination_keywords_and_more'),
    ]

    operations = [
        migrations.RunPython(add_explore_content, migrations.RunPython.noop),
    ]
