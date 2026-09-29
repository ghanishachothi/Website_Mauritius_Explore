"""Moves the Taste Mauritius food cards into the general Experience table (category "Food")
and removes the old FoodExperience table. Food page is now /experiences/category/food/."""
from django.db import migrations

OLD_PHOTOS = {
    "mine-bouille": "images/food/mine-bouille.jpg",
    "traditional-7-cari": "images/food/traditional-7-cari.jpg",
    "mauritian-biryani": "images/food/mauritian-biryani.png",
    "mauritian-tea": "images/food/mauritian-tea.png",
    "local-market-food-experience": "images/food/local-market-food-experience.png",
}
KIND = {"cuisine": "Mauritian Cuisine", "quest": "Food Quests"}


def forward(apps, schema_editor):
    Category = apps.get_model("experiences", "Category")
    Experience = apps.get_model("experiences", "Experience")
    FoodExperience = apps.get_model("experiences", "FoodExperience")

    cat = (Category.objects.filter(slug="food").first()
           or Category.objects.filter(name__iexact="food").first()
           or Category(name="Food", slug="food"))
    cat.slug = cat.slug or "food"
    cat.hero_title = cat.hero_title or "TASTE MAURITIUS"
    cat.hero_subtitle = cat.hero_subtitle or "Discover the flavours, dishes and food traditions of the island"
    cat.hero_image = cat.hero_image or "images/food/hero.jpg"
    cat.save()

    for f in FoodExperience.objects.all():
        Experience.objects.update_or_create(slug=f.slug, defaults=dict(
            category=cat, name=f.name, kind=KIND.get(f.kind, f.kind), location=f.location,
            rating=f.rating, price=f.price or None, description=f.description,
            image=f.image.name if f.image else "",
            static_image=f.static_image or OLD_PHOTOS.get(f.slug, ""),
            is_active=f.is_active, order=f.order))

    WayToExplore = apps.get_model("destinations", "WayToExplore")
    WayToExplore.objects.filter(url="/experiences/food/").update(url="/experiences/category/food/")


class Migration(migrations.Migration):

    dependencies = [
        ("experiences", "0005_merge_0002_category_icon_0004_more_food"),
        ("experiences", "0004_category_accent_color_category_accent_light"),
        ("destinations", "0004_explore_content"),
    ]

    operations = [
        migrations.RunPython(forward, migrations.RunPython.noop),
        migrations.DeleteModel(name="FoodExperience"),
    ]
