import os, django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mauritius_explore.settings"); django.setup()
from apps.explore.models import SitePage
from apps.explore.models import Destination

# ---------- header: exactly like the Figma ----------
SitePage.objects.filter(location__in=["header1", "header2"]).delete()
header = [
    # name, url, set, line 1, line 2
    ("Discover Mauritius", "/", "header1", "Discover", "Mauritius"),
    ("Experience Insight", "/experiences/", "header1", "Experience", "Insight"),
    ("Explore The Island", "/destinations/", "header1", "Explore", "The Island"),
    ("Guides & Packages", "/destinations/guides-packages/", "header1", "Guides &", "Packages"),
    ("Island Calendar", "/experiences/calendar/", "header1", "Island", "Calendar"),
    ("Explore Board", "/destinations/board/", "header2", "Explore", "Board"),
    ("Explore Your Way", "/experiences/", "header2", "Explore", "Your Way"),
]
for i, (name, url, where, l1, l2) in enumerate(header):
    SitePage.objects.create(name=name, url=url, location=where,
                            header_line1=l1, header_line2=l2, order=i)
    print("header:", where, "|", name)

# ---------- swap the photos of Marine Park and Sega by the Sea ----------
a = Destination.objects.get(name="Marine Park")
b = Destination.objects.get(name="Sega by the Sea")
a.image, b.image = b.image, a.image
a.save(); b.save()
print("swapped: Marine Park <-> Sega by the Sea")
print("DONE - press Ctrl+F5")
