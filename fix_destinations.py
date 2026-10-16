import os, sys, glob, subprocess
from pathlib import Path

if len(sys.argv) == 1:
    # ---------- 1. models: add "area" + "order" to Destination ----------
    p = Path("apps/destinations/models.py"); s = p.read_text(encoding="utf-8-sig")
    if "area = models.CharField" not in s:
        s = s.replace(
            "    is_featured = models.BooleanField(default=False, help_text='Show on the homepage')\n\n    class Meta:\n        ordering = ['name']",
            "    is_featured = models.BooleanField(default=False, help_text='Show on the homepage')\n"
            "    area = models.CharField(max_length=100, blank=True, help_text='Text under the name on the card, e.g. Blue Bay')\n"
            "    order = models.PositiveIntegerField(default=0, help_text='Top Destinations order (lower = first)')\n\n"
            "    class Meta:\n        ordering = ['order', 'name']", 1)
        p.write_text(s, encoding="utf-8"); print("models.py:", "OK" if "area = models" in s else "NOT CHANGED")
    # ---------- 2. admin: edit area/order in the list ----------
    p = Path("apps/destinations/admin.py"); s = p.read_text(encoding="utf-8-sig")
    s = s.replace("list_display = ('name', 'region', 'is_featured')", "list_display = ('name', 'area', 'region', 'order', 'is_featured')")
    s = s.replace("    list_filter = ('region', 'is_featured')\n    list_editable = ('is_featured',)",
                  "    list_filter = ('region', 'is_featured')\n    list_editable = ('area', 'order', 'is_featured')")
    p.write_text(s, encoding="utf-8"); print("admin.py: OK")
    # ---------- 3. view: use the order + the area text ----------
    p = Path("apps/core/views.py"); s = p.read_text(encoding="utf-8-sig")
    s = s.replace(".filter(is_featured=True).order_by('name')[:10]", ".filter(is_featured=True).order_by('order', 'name')[:12]")
    s = s.replace("'area': place.region.name,", "'area': place.area or place.region.name,")
    p.write_text(s, encoding="utf-8"); print("views.py: OK")
    # ---------- 4. database ----------
    subprocess.run([sys.executable, "manage.py", "makemigrations", "destinations"], check=True)
    subprocess.run([sys.executable, "manage.py", "migrate"], check=True)
    subprocess.run([sys.executable, __file__, "data"], check=True)
    sys.exit()

# ---------- 5. data: the cards, in your Figma order ----------
import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mauritius_explore.settings"); django.setup()
from django.conf import settings
from django.core.files import File
from apps.explore.models import Region, Destination

IMG = Path(settings.BASE_DIR) / "static" / "images"
R = {n: Region.objects.get_or_create(name=n, defaults={"order": i})[0] for i, n in enumerate(["North", "South", "East", "West", "Central"])}
WA = sorted(Path(x).name for x in glob.glob(str(IMG / "WhatsApp_Image*")))
wa = lambda i: WA[i] if i < len(WA) else None

items = [  # name, old names in the database, text under the name, region, photo
    ("Marine Park", [], "Blue Bay", "South", wa(0)),
    ("Caudan", [], "Port Louis", "North", wa(1)),
    ("Sega by the Sea", [], "Belle-Mare", "East", wa(2)),
    ("Macconde Viewpoint", [], "Baie du Cap, Mauritius", "South", wa(3)),
    ("Le Morne Brabant", ["Le Morne"], "Le Morne, South-West", "West", "le-morne.jpg"),
    ("Seven Coloured Earth", [], "Chamarel", "West", "seven-coloured-earth.jpg"),
    ("Grand Bassin", [], "Savanne", "South", "grand-bassin.jpg"),
    ("Belle Mare Beach", ["Belle Mare"], "Flacq, East Coast", "East", "belle-mare.jpg"),
    ("Botanical Garden", ["Pamplemousses Garden"], "Pamplemousses", "North", "pamplemousses-garden.jpg"),
    ("Chamarel Waterfall", [], "Chamarel", "West", "chamarel-waterfall.jpg"),
    ("Ile aux Cerfs", [], "Trou d'Eau Douce, East Coast", "East", "ile-aux-cerfs.jpg"),
]
Destination.objects.update(is_featured=False)
Destination.objects.filter(name="Trou aux Cerfs").update(image="")
for i, (name, old, area, region, img) in enumerate(items):
    d = Destination.objects.filter(name__in=[name] + old).first() or Destination(name=name, region=R[region])
    d.name, d.area, d.region, d.order, d.is_featured = name, area, R[region], i, True
    if img and (IMG / img).exists():
        with open(IMG / img, "rb") as f:
            d.image.save(img, File(f), save=False)
    d.save()
    print(f"{i+1:2}. {name:22} | {area:30} | {img}")
print("DONE - open http://127.0.0.1:8001/ and press Ctrl+F5")
