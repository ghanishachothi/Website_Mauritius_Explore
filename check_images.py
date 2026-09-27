import os, re, shutil, glob, django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mauritius_explore.settings")
django.setup()
from pathlib import Path
from django.conf import settings
from django.core.files import File
from django.test import Client
from apps.destinations.models import Destination

BASE = Path(settings.BASE_DIR)
IMG = BASE / "static" / "images"

# 1. every destination gets its photo (matched by name)
match = [("morne", "le-morne.jpg"), ("belle", "belle-mare.jpg"), ("waterfall", "chamarel-waterfall.jpg"),
         ("colour", "seven-coloured-earth.jpg"), ("bassin", "grand-bassin.jpg"),
         ("cerfs", "ile-aux-cerfs.jpg"), ("pamplemousse", "pamplemousses-garden.jpg")]
for d in Destination.objects.all():
    for word, filename in match:
        if word in d.name.lower() and (IMG / filename).exists():
            with open(IMG / filename, "rb") as f:
                d.image.save(filename, File(f), save=True)
            print("photo ->", d.name, "=", d.image.url)
            break

# 2. every template: logo.png -> image_11.jpg
for t in glob.glob(str(BASE / "templates" / "**" / "*.html"), recursive=True) + \
         glob.glob(str(BASE / "apps" / "**" / "*.html"), recursive=True):
    s = open(t, encoding="utf-8-sig").read()
    if "images/logo.png" in s or "images/app/icon-192.png" in s:
        s = s.replace("images/logo.png", "images/image_11.jpg").replace("images/app/icon-192.png", "images/image_11.jpg")
        open(t, "w", encoding="utf-8").write(s)
        print("logo fixed in", t)

# 3. load the homepage and check every picture
html = Client(HTTP_HOST="127.0.0.1").get("/").content.decode()
print("\nDEBUG =", settings.DEBUG, "| MEDIA_ROOT =", settings.MEDIA_ROOT)
bad = 0
for src in sorted(set(re.findall(r'src="([^"]+)"', html))):
    if src.startswith("/static/"):
        ok = (BASE / "static" / src[len("/static/"):]).exists()
    elif src.startswith("/media/"):
        ok = (Path(settings.MEDIA_ROOT) / src[len("/media/"):]).exists()
    else:
        continue
    print("OK     " if ok else "MISSING", src)
    bad += not ok
print("\nALL PICTURES FOUND - press Ctrl+F5" if not bad else f"\n{bad} picture(s) missing - paste me this output")
