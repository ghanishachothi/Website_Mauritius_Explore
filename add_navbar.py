"""
Explore Board nav bar on Explore the Island + Taste Mauritius (not the homepage).
Put next to manage.py and run:  python add_navbar.py   (then delete it)
"""
import os, sys
if not os.path.exists("manage.py"):
    sys.exit("Run this from the project folder (the one with manage.py).")

PARTIAL = r"""{% load static %}
{# Nav bar from the Explore Board frame - used by Explore the Island and Taste Mauritius. #}
{# Links come from /admin/ -> Site pages -> "Side menu (Explore the site)". #}
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.2/css/all.min.css">
<link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600&display=swap" rel="stylesheet">
<link rel="stylesheet" href="{% static 'css/eb_navbar.css' %}">

<header class="eb-navbar">
    <a href="{% url 'core:home' %}" class="eb-logo">
        <span class="eb-logo-badge">
            <img src="{% static 'images/image_11.jpg' %}" alt="Mauritius Explore logo">
        </span>
        <span class="eb-logo-text">Mauritius<br><span>Explore</span></span>
    </a>

    <button type="button" class="eb-nav-arrow" id="navPrev" aria-label="Previous pages">
        <i class="fa-solid fa-chevron-left"></i>
    </button>

    <nav class="eb-nav-track" id="navTrack">
        {% for page in menu_pages %}{% if page.url != '/dashboard/' or user.is_staff %}
            <a href="{{ page.url }}" class="eb-nav-link{% if request.path == page.url %} active{% endif %}"
               {% if request.path == page.url %}aria-current="page"{% endif %}>{{ page.name }}</a>
        {% endif %}{% endfor %}
    </nav>

    <button type="button" class="eb-nav-arrow" id="navNext" aria-label="Next pages">
        <i class="fa-solid fa-chevron-right"></i>
    </button>

    <!-- Profile icon: click to see the customer's account -->
    <div class="eb-account">
        <button type="button" class="eb-profile-btn" id="ebAccountBtn"
                aria-expanded="false" aria-controls="ebAccountPanel" aria-label="My account">
            <i class="fa-solid fa-user"></i>
        </button>

        <div class="eb-dropdown eb-account-panel" id="ebAccountPanel" hidden>
            {% if user.is_authenticated %}
                <p class="eb-account-name">{{ user.get_full_name|default:user.username }}</p>
                <p class="eb-account-sub">{{ user.email|default:user.username }}</p>
                <p class="eb-account-sub">{{ user.profile.get_role_display }} &bull; Member since {{ user.date_joined|date:"M Y" }}</p>
                <div class="eb-dropdown-divider"></div>
                <a href="{% url 'users:profile' %}" class="eb-account-link">My Profile</a>
                <a href="{% url 'experiences:my_experiences' %}" class="eb-account-link">My Experiences</a>
                {% if user.is_staff %}<a href="{% url 'admin_dashboard:dashboard' %}" class="eb-account-link">Dashboard</a>{% endif %}
                <form method="post" action="{% url 'users:logout' %}">
                    {% csrf_token %}
                    <button type="submit" class="eb-account-link eb-logout">Log out</button>
                </form>
            {% else %}
                <p class="eb-account-name">Welcome, Explorer</p>
                <p class="eb-account-sub">Log in to see your account</p>
                <div class="eb-dropdown-divider"></div>
                <a href="{% url 'users:login' %}" class="eb-account-link">Log in</a>
                <a href="{% url 'users:signup' %}" class="eb-account-link">Create Account</a>
            {% endif %}
        </div>
    </div>

    <!-- 3 bars: the same side menu as every page -->
    <button type="button" class="eb-menu-btn" id="menuBtn" aria-label="Open menu"
            aria-expanded="false" aria-controls="sideMenu">
        <span></span><span></span><span></span>
    </button>
</header>

<script>
  (function () {
    /* arrows scroll the page titles; the bar starts two tabs before the page you are on */
    const track = document.getElementById('navTrack');
    const step = 260;
    document.getElementById('navPrev').addEventListener('click', () => track.scrollBy({ left: -step }));
    document.getElementById('navNext').addEventListener('click', () => track.scrollBy({ left: step }));
    function alignNav() {
      const links = [...track.querySelectorAll('.eb-nav-link')];
      const i = links.findIndex(a => a.classList.contains('active'));
      if (i < 2) return;
      const offset = links[i - 2].getBoundingClientRect().left - track.getBoundingClientRect().left;
      track.style.scrollBehavior = 'auto';
      track.scrollLeft += offset - 10;
      track.style.scrollBehavior = '';
    }
    alignNav();
    window.addEventListener('load', alignNav);

    /* profile icon: click to open, click again / anywhere else / Escape to close */
    const btn = document.getElementById('ebAccountBtn');
    const panel = document.getElementById('ebAccountPanel');
    const close = () => { panel.hidden = true; btn.setAttribute('aria-expanded', 'false'); };
    btn.addEventListener('click', e => {
      e.stopPropagation();
      const open = panel.hidden;
      panel.hidden = !open;
      btn.setAttribute('aria-expanded', open ? 'true' : 'false');
    });
    panel.addEventListener('click', e => e.stopPropagation());
    document.addEventListener('click', close);
    document.addEventListener('keydown', e => { if (e.key === 'Escape') close(); });
  })();
</script>
"""
CSS = r"""/* ============ Explore Board nav bar (Explore the Island + Taste Mauritius) ============
   Loaded only by templates/partials/eb_navbar.html. Everything is scoped to .eb-navbar. */

.eb-navbar{
  --eb-navy:#0b1760; --eb-heading:#2b3f86; --eb-muted:#5d6b8a; --eb-teal:#19a7c7; --eb-card:#f1f3f6;
  --eb-serif:"Playfair Display", Georgia, serif; --eb-sans:"Poppins", Arial, sans-serif;
  position:relative; z-index:30;
  display:flex; align-items:center; gap:20px;
  height:80px; padding:0 28px;
  background:linear-gradient(90deg, #d8e6f7 0%, #c4d9f3 100%);
  font-family:var(--eb-sans);
}
.eb-navbar a{ color:inherit; text-decoration:none; }
.eb-navbar .eb-logo{ display:flex; align-items:center; gap:10px; flex-shrink:0; }
.eb-navbar .eb-logo-badge{
  width:58px; height:58px; border-radius:6px; flex-shrink:0;
  background:#fff; display:grid; place-items:center; padding:3px;
}
.eb-navbar .eb-logo-badge img{ width:100%; height:100%; object-fit:contain; display:block; }
.eb-navbar .eb-logo-text{ font-family:var(--eb-serif); font-size:20px; line-height:1.05; color:var(--eb-heading); font-weight:700; }
.eb-navbar .eb-logo-text span{ color:var(--eb-teal); }

.eb-navbar .eb-nav-arrow{
  width:32px; height:32px; border-radius:50%; border:none; flex-shrink:0;
  background:var(--eb-navy); color:#fff; font-size:13px; cursor:pointer;
  transition:transform .15s;
}
.eb-navbar .eb-nav-arrow:hover{ transform:scale(1.1); }

.eb-navbar .eb-nav-track{
  flex:1; display:flex; gap:60px; overflow-x:auto; scroll-behavior:smooth;
  scrollbar-width:none; padding:0 10px; align-items:center;
  -webkit-mask-image:linear-gradient(90deg, transparent 0, #000 40px, #000 calc(100% - 40px), transparent 100%);
          mask-image:linear-gradient(90deg, transparent 0, #000 40px, #000 calc(100% - 40px), transparent 100%);
}
.eb-navbar .eb-nav-track::-webkit-scrollbar{ display:none; }
.eb-navbar .eb-nav-link{
  flex-shrink:0; font-family:var(--eb-serif); font-size:19px; color:var(--eb-heading);
  text-align:center; max-width:160px; line-height:1.15; padding:8px 4px 10px;
  border-bottom:4px solid transparent; transition:color .15s;
}
.eb-navbar .eb-nav-link:hover{ color:var(--eb-teal); }
.eb-navbar .eb-nav-link.active{ border-bottom-color:#5b8ee6; font-weight:700; }

.eb-navbar .eb-account{ position:relative; flex-shrink:0; }
.eb-navbar .eb-profile-btn{
  width:40px; height:40px; border-radius:50%; border:none; cursor:pointer;
  background:#fff; color:var(--eb-navy); font-size:17px; display:grid; place-items:center;
  transition:box-shadow .15s;
}
.eb-navbar .eb-profile-btn:hover,
.eb-navbar .eb-profile-btn[aria-expanded="true"]{ box-shadow:0 0 0 3px rgba(11,23,96,.18); }

.eb-navbar .eb-dropdown{
  position:absolute; z-index:40; top:calc(100% + 10px); right:0;
  width:240px; padding:14px;
  background:#fff; border-radius:12px;
  box-shadow:0 10px 28px rgba(11,23,96,.18);
  animation:eb-drop .18s ease-out;
}
.eb-navbar .eb-dropdown[hidden]{ display:none; }
@keyframes eb-drop{ from{ opacity:0; transform:translateY(-6px); } to{ opacity:1; transform:none; } }
.eb-navbar .eb-account-name{ font-family:var(--eb-serif); font-size:15px; font-weight:700; color:var(--eb-navy); }
.eb-navbar .eb-account-sub{ font-size:12px; color:var(--eb-muted); }
.eb-navbar .eb-dropdown-divider{ height:1px; background:#e6e9f0; margin:10px 0 6px; }
.eb-navbar .eb-account-link{
  display:block; width:100%; text-align:left; padding:7px 8px; border-radius:6px;
  font:500 13px var(--eb-sans); color:var(--eb-navy); background:none; border:none; cursor:pointer;
}
.eb-navbar .eb-account-link:hover{ background:var(--eb-card); }
.eb-navbar .eb-logout{ color:#c62828; }
.eb-navbar form{ margin:0; }

/* 3 bars: opens the shared side menu */
.eb-navbar .eb-menu-btn{
  flex-shrink:0; background:none; border:none; cursor:pointer;
  display:flex; flex-direction:column; gap:5px; padding:4px;
}
.eb-navbar .eb-menu-btn span{ display:block; width:26px; height:2.5px; background:var(--eb-navy); border-radius:2px; }

.eb-navbar button:focus-visible, .eb-navbar a:focus-visible{ outline:2px solid var(--eb-teal); outline-offset:2px; }

@media (max-width:700px){
  .eb-navbar{ gap:10px; padding:0 12px; }
  .eb-navbar .eb-logo-text{ display:none; }
  .eb-navbar .eb-nav-link{ font-size:16px; }
  .eb-navbar .eb-nav-track{ gap:28px; }
}
"""

def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    open(path, "w", encoding="utf-8").write(text)
    print("written      " + path)

def edit(path, changes):
    s = open(path, encoding="utf-8-sig").read()
    for old, new, done in changes:
        if done in s:
            continue
        if old not in s:
            sys.exit("STOP - could not find the spot to change in " + path + ":\n  " + old[:70] + "\nPaste me this message.")
        s = s.replace(old, new, 1)
    open(path, "w", encoding="utf-8").write(s)
    print("updated      " + path)

write("templates/partials/eb_navbar.html", PARTIAL)
write("static/css/eb_navbar.css", CSS)

# base.html: pages may replace the header; the menu/account code copes when a page has another header
s = open("templates/base.html", encoding="utf-8-sig").read()
if "{% block header %}" not in s:
    start = s.index('<header class="site-header">')
    end = s.index("</header>", start) + len("</header>")
    s = s[:start] + "{% block header %}\n" + s[start:end] + "\n{% endblock %}" + s[end:]
    open("templates/base.html", "w", encoding="utf-8").write(s)
    print("updated      templates/base.html (header block)")
edit("templates/base.html", [
    ("function closeAccount() {\n    accountMenu.classList.remove('open');",
     "function closeAccount() {\n    if (!accountMenu) return;\n    accountMenu.classList.remove('open');",
     "if (!accountMenu) return;"),
    ("  accountBtn.addEventListener('click', e => {",
     "  if (accountBtn) accountBtn.addEventListener('click', e => {", "if (accountBtn) accountBtn"),
    ("  accountMenu.addEventListener('click', e => e.stopPropagation());",
     "  if (accountMenu) accountMenu.addEventListener('click', e => e.stopPropagation());", "if (accountMenu) accountMenu.addEventListener"),
    ("  navNextBtn.addEventListener('click', () => {",
     "  if (navNextBtn) navNextBtn.addEventListener('click', () => {", "if (navNextBtn) navNextBtn"),
    ("    menuBtn.setAttribute('aria-expanded', open);",
     "    if (menuBtn) menuBtn.setAttribute('aria-expanded', open);", "if (menuBtn) menuBtn.setAttribute"),
    ("  menuBtn.addEventListener('click', () => { closeAccount(); setSideMenu(true); });",
     "  if (menuBtn) menuBtn.addEventListener('click', () => { closeAccount(); setSideMenu(true); });", "if (menuBtn) menuBtn.addEventListener"),
])

HEADER = "{% block header %}{% include 'partials/eb_navbar.html' %}{% endblock %}\n"
edit("apps/destinations/templates/destinations/explore_island.html",
     [("{% block main_class %}explore-main{% endblock %}\n",
       "{% block main_class %}explore-main{% endblock %}\n\n" + HEADER, "partials/eb_navbar.html")])
edit("apps/experiences/templates/experiences/food.html",
     [("{% block main_class %}food-main{% endblock %}\n",
       "{% block main_class %}food-main{% endblock %}\n\n" + HEADER, "partials/eb_navbar.html")])

# the new bar sits above the page (not over it), so these pages need less space at the top
for path, marker, extra in [
    ("static/css/explore.css", "/* eb navbar spacing */",
     "\n/* eb navbar spacing */\nmain.explore-main{ padding-top:24px; }\n@media (max-width:900px){ main.explore-main{ padding-top:20px; } }\n"),
    ("static/css/food.css", "/* eb navbar spacing */",
     "\n/* eb navbar spacing */\n.food-main .food-hero{ padding-top:48px; }\n@media (max-width:900px){ .food-main .food-hero{ padding-top:48px; } }\n"),
]:
    c = open(path, encoding="utf-8-sig").read()
    if marker not in c:
        open(path, "w", encoding="utf-8").write(c + extra)
        print("updated      " + path)

print("\nDONE - press Ctrl+F5 on /destinations/ and /experiences/food/ (the homepage keeps its own header)")
