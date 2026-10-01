import os, django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mauritius_explore.settings")
django.setup()
from apps.destinations.models import Region
from apps.core.models import SitePage

# ---------- 1. home.html: left arrow + one-card-per-click ----------
p = "apps/core/templates/core/home.html"
s = open(p, encoding="utf-8-sig").read()
if "arrow-left" in s:
    print("home.html: already fixed")
else:
    left_btn = '''<button class="arrow arrow-left" aria-label="Show previous destinations">
        <svg viewBox="0 0 24 24" fill="none" stroke="#1a1a1a" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><polyline points="15 5 8 12 15 19"></polyline></svg>
      </button>
      <div class="cards" id="cards">'''
    new_js = """const track = document.getElementById('cards');
  // one click = one card
  function cardStep() {
    const card = track.querySelector('.dest-card');
    return card ? card.getBoundingClientRect().width + 18 : track.clientWidth;
  }
  document.querySelector('.arrow-left').addEventListener('click', () => {
    if (track.scrollLeft <= 5) {
      track.scrollTo({ left: track.scrollWidth, behavior: 'smooth' });
    } else {
      track.scrollBy({ left: -cardStep(), behavior: 'smooth' });
    }
  });"""
    steps = [
        ('<div class="cards" id="cards">', left_btn),
        ("const track = document.getElementById('cards');", new_js),
        ("track.scrollBy({ left: track.clientWidth, behavior: 'smooth' });",
         "track.scrollBy({ left: cardStep(), behavior: 'smooth' });"),
    ]
    for old, new in steps:
        if old in s:
            s = s.replace(old, new, 1)
            print("home.html: OK   ", old[:45])
        else:
            print("home.html: NOT FOUND ->", old[:45])
    open(p, "w", encoding="utf-8").write(s)

# ---------- 2. style.css: the card design ----------
c = "static/css/style.css"
css = open(c, encoding="utf-8-sig").read()
marker = "/* ===== TOP DESTINATIONS FIX ===== */"
if marker in css:
    print("style.css: already fixed")
else:
    css += "\n" + marker + """
.top-destinations .carousel{ position:relative; flex:1; min-width:0; display:flex; align-items:center; padding:0 34px; }
.top-destinations .cards{ display:flex; gap:18px; width:100%; overflow-x:auto; scroll-behavior:smooth;
  scrollbar-width:none; scroll-snap-type:x mandatory; padding:6px 4px; }
.top-destinations .cards::-webkit-scrollbar{ display:none; }
.top-destinations .dest-card{ position:relative; flex:0 0 calc((100% - 3 * 18px) / 4); min-width:200px;
  height:360px; border-radius:22px; overflow:hidden; background:#cfd8dc;
  box-shadow:0 4px 14px rgba(0,0,0,.18); scroll-snap-align:start; }
.top-destinations .dest-card img{ position:absolute; inset:0; width:100%; height:100%; max-width:none;
  object-fit:cover; transition:transform .4s; }
.top-destinations .dest-card:hover img{ transform:scale(1.06); }
.top-destinations .dest-card::after{ content:""; position:absolute; left:0; right:0; bottom:0; height:45%;
  background:linear-gradient(to top, rgba(0,0,0,.72), rgba(0,0,0,0)); pointer-events:none; }
.top-destinations .card-link{ position:absolute; inset:0; z-index:3; }
.top-destinations .card-caption{ position:absolute; z-index:2; left:0; right:0; bottom:18px; display:flex;
  align-items:flex-start; gap:10px; padding:0 16px; color:#fff; text-shadow:0 2px 5px rgba(0,0,0,.65); }
.top-destinations .card-caption p{ margin:0; line-height:1.25; }
.top-destinations .card-caption .pin{ width:18px; height:18px; flex:0 0 auto; margin-top:2px; }
.top-destinations .card-caption .place{ font-family:var(--font-serif); font-weight:700; font-size:17px; }
.top-destinations .card-caption .area{ font-family:var(--font-serif); font-weight:600; font-size:14px; }
.top-destinations .arrow{ position:absolute; top:50%; transform:translateY(-50%); width:52px; height:52px;
  border:none; border-radius:50%; background:#fff; box-shadow:0 3px 10px rgba(0,0,0,.25);
  display:grid; place-items:center; cursor:pointer; z-index:6; }
.top-destinations .arrow svg{ width:22px; height:22px; }
.top-destinations .arrow:hover{ background:#f3f5fb; }
.top-destinations .arrow-left{ left:0; }
.top-destinations .arrow-right{ right:0; }
@media (max-width:1200px){ .top-destinations .dest-card{ flex-basis:calc((100% - 2 * 18px) / 3); } }
@media (max-width:900px){ .top-destinations .dest-card{ flex-basis:calc((100% - 18px) / 2); height:300px; } }
"""
    open(c, "w", encoding="utf-8").write(css)
    print("style.css: OK")

# ---------- 3. header: North / South / East / West / Central ----------
for i, r in enumerate(Region.objects.all()):
    SitePage.objects.update_or_create(name=f"{r.name} Mauritius", defaults={
        "url": r.get_absolute_url(), "location": "header2", "header_line1": r.name,
        "header_line2": "", "order": i, "icon": "map", "keywords": "region"})
print("header regions:", SitePage.objects.filter(location="header2").count())
print("DONE - now press Ctrl+F5 in the browser")
