"""
Fills the database with the Island Calendar categories and events.

RUN IT ONCE:
    python add_events.py

Before running, put your six photos in:
    static/images/events/

It is safe to run twice - it updates the same rows instead of making
duplicates. Change anything afterwards in /admin/.
"""
import os
from datetime import date, time
from pathlib import Path

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mauritius_explore.settings")
django.setup()

from django.conf import settings                      # noqa: E402
from django.core.files import File                    # noqa: E402
from apps.explore.models import Destination      # noqa: E402
from apps.explore.models import Category, Event   # noqa: E402

PHOTOS = Path(settings.BASE_DIR) / "static" / "images" / "events"


# ----------------------------------------------------------------------
# 1. CATEGORIES - the filter pills and the "What to expect" tiles
# ----------------------------------------------------------------------
CATEGORIES = [
    # name,                 emoji
    ("Nightlife & Parties", "🎧"),
    ("Food & Street Eats",  "🍛"),
    ("Nature & Outdoor",    "🥾"),
    ("Culture & Arts",      "🎭"),
    ("Wellness & Lifestyle", "🧘"),
    ("Secret & Pop-Ups",    "🎁"),
    ("Festival",            "🎉"),
    ("Live Music",          "🎶"),
]


# ----------------------------------------------------------------------
# 2. EVENTS
#    region is used to pick a destination, which is what the
#    "All Mauritius" dropdown filters on.
# ----------------------------------------------------------------------
EVENTS = [
    {
        "title": "Neon Nights at OMG",
        "category": "Nightlife & Parties",
        "region": "North",
        "location": "Grand Baie Coastal Road",
        "date": date(2026, 10, 16),
        "start": time(22, 0),
        "end": time(4, 0),
        "price": 1200,
        "photo": "Neon.png",
        "blurb": "Mauritius' biggest beachfront club night.",
    },
    {
        "title": "The Secret Mauritian Feast",
        "category": "Secret & Pop-Ups",
        "region": "Central",
        "location": "Revealed 2h before",
        "date": date(2026, 10, 18),
        "start": time(18, 0),
        "end": time(23, 30),
        "price": 950,
        "photo": "Mauritius Food.png",
        "blurb": "A pop-up dinner in a location you learn on the day.",
    },
    {
        "title": "Pitons & Valleys Sunrise Hike",
        "category": "Nature & Outdoor",
        "region": "West",
        "location": "Black River Gorges",
        "date": date(2026, 10, 21),
        "start": time(5, 30),
        "end": time(9, 0),
        "price": 800,
        "photo": "Piton.png",
        "blurb": "Guided climb to catch the sun over the gorges.",
    },
    {
        "title": "Live Music Sunset Session",
        "category": "Live Music",
        "region": "West",
        "location": "Flic-en-Flac",
        "date": date(2026, 10, 17),
        "start": time(17, 0),
        "end": time(23, 0),
        "price": 1500,
        "photo": "Live Music.png",
        "blurb": "Sega and jazz on the sand as the sun goes down.",
    },
    {
        "title": "Zipline Adventure",
        "category": "Nature & Outdoor",
        "region": "South",
        "location": "Vallée Adventure Park",
        "date": date(2026, 10, 17),
        "start": time(9, 0),
        "end": time(15, 0),
        "price": 1800,
        "photo": "Zipline.png",
        "blurb": "Five lines across the valley, longest 400m.",
    },
    {
        "title": "La Croisette Food Festival",
        "category": "Food & Street Eats",
        "region": "North",
        "location": "Grand Baie",
        "date": date(2026, 10, 18),
        "start": time(12, 0),
        "end": time(23, 0),
        "price": 600,
        "photo": "Food Festival.png",
        "blurb": "Street food from every corner of the island.",
    },
]


def pick_destination(region_name):
    """Any destination in that region, so the region filter works."""
    return (Destination.objects
            .filter(region__name__iexact=region_name)
            .first())


def main():
    print("Categories")
    print("-" * 52)
    categories = {}
    for name, icon in CATEGORIES:
        category, created = Category.objects.get_or_create(name=name)
        category.icon = icon
        category.save()
        categories[name] = category
        print(f"  {icon}  {name:<24} {'added' if created else 'updated'}")

    print()
    print("Events")
    print("-" * 52)
    missing_photos = []
    no_destination = []

    for row in EVENTS:
        event, created = Event.objects.get_or_create(
            title=row["title"],
            defaults={"date": row["date"], "price": row["price"]},
        )

        event.category = categories[row["category"]]
        event.date = row["date"]
        event.start_time = row["start"]
        event.end_time = row["end"]
        event.location_name = row["location"]
        event.price = row["price"]
        event.short_description = row["blurb"]
        event.capacity = 20
        event.is_featured = True

        destination = pick_destination(row["region"])
        if destination:
            event.destination = destination
        else:
            no_destination.append((row["title"], row["region"]))

        photo = PHOTOS / row["photo"]
        if not event.image and photo.exists():
            with open(photo, "rb") as f:
                event.image.save(row["photo"], File(f), save=False)
        elif not photo.exists():
            missing_photos.append(row["photo"])

        event.save()
        print(f"  {event.date}  {row['title']:<32} {'added' if created else 'updated'}")

    print()
    print(f"Done. {Category.objects.count()} categories, {Event.objects.count()} events.")

    if missing_photos:
        print()
        print("No photo found for these - add them in /admin/:")
        for name in missing_photos:
            print(f"  missing: static/images/events/{name}")

    if no_destination:
        print()
        print("No destination in these regions, so the region filter will skip them:")
        for title, region in no_destination:
            print(f"  {title} (wanted {region})")
        print("  Add destinations in /admin/, then run this again.")


if __name__ == "__main__":
    main()