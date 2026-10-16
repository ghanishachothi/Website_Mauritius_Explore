import os, django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mauritius_explore.settings")
django.setup()
from django.conf import settings
from django.core.files import File
from apps.explore.models import Region, Destination
from apps.explore.models import SocialLink, FooterColumn, FooterLink

IMG = settings.BASE_DIR / "static" / "images"
regions = {n: Region.objects.get_or_create(name=n, defaults={"order": i})[0]
           for i, n in enumerate(["North", "South", "East", "West", "Central"])}

# ---- Top Destinations: your photos ----
places = [
    ("Belle Mare", "East", "belle-mare.jpg", -20.1900, 57.7700),
    ("Chamarel Waterfall", "West", "chamarel-waterfall.jpg", -20.4430, 57.3900),
    ("Grand Bassin", "South", "grand-bassin.jpg", -20.4180, 57.4910),
    ("Ile aux Cerfs", "East", "ile-aux-cerfs.jpg", -20.2717, 57.8045),
    ("Le Morne", "West", "le-morne.jpg", -20.4561, 57.3150),
    ("Pamplemousses Garden", "North", "pamplemousses-garden.jpg", -20.1040, 57.5800),
    ("Seven Coloured Earth", "West", "seven-coloured-earth.jpg", -20.4400, 57.3730),
]
Destination.objects.update(is_featured=False)
for name, region, filename, lat, lng in places:
    d, _ = Destination.objects.get_or_create(name=name, defaults={
        "region": regions[region], "latitude": lat, "longitude": lng})
    d.region = regions[region]
    d.is_featured = True
    if not d.image:
        with open(IMG / filename, "rb") as f:
            d.image.save(filename, File(f), save=False)
    d.save()
    print("photo ->", name)

# ---- Social icons (files are in static/images/) ----
SocialLink.objects.filter(platform="tiktok").delete()
for i, p in enumerate(["facebook", "whatsapp", "gmail", "instagram"]):
    SocialLink.objects.update_or_create(platform=p, defaults={
        "icon": f"images/{p}.png", "show_in_footer": True, "order": i,
        "url": {"facebook": "https://www.facebook.com/", "whatsapp": "https://wa.me/",
                "gmail": "mailto:", "instagram": "https://www.instagram.com/"}[p]})

# ---- Footer columns exactly like the Figma frame ----
ev, gp, bd = "/experiences/", "/destinations/guides-packages/", "/destinations/board/"
footer = {
    "Explore Mauritius": [("Discover Mauritius", "/"), ("Explore Experiences", ev),
        ("Top Destinations", "/#top-destinations"), ("Things to Do", ev),
        ("Hidden Gems of Mauritius", bd), ("Island Activities", "/experiences/calendar/"),
        ("Local Attractions", "/destinations/")],
    "Experiences": [("Beach & Water Activities", ev + "?category=water-sports"),
        ("Nature & Adventure", ev + "?category=hiking"), ("Cultural Experiences", ev + "?category=culture"),
        ("Food & Local Cuisine", ev + "?category=food"), ("Hiking & Outdoor Adventures", ev + "?category=hiking"),
        ("Family Activities", ev), ("Romantic Experiences", ev)],
    "Guides": [("Local Guides", gp), ("Find a Guide", gp), ("Explore with Locals", gp),
        ("Guide Recommendations", gp), ("Guided Tours", gp), ("Travel Tips", "#help"),
        ("Useful Information", "#help")],
    "Mauritius Explorer": [("About Us", "#help"), ("Contact Us", "#help"), ("Our Mission", "#help"),
        ("Become a Guide", "#help"), ("Become a Partner", "#help"),
        ("Privacy Policy", "#help"), ("Terms & Conditions", "#help")],
}
FooterColumn.objects.all().delete()
for i, (title, links) in enumerate(footer.items()):
    col = FooterColumn.objects.create(title=title, order=i)
    for j, (label, url) in enumerate(links):
        FooterLink.objects.create(column=col, label=label, url=url, order=j)
print("Done: photos, social icons and footer updated.")
