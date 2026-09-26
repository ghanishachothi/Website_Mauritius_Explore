from datetime import datetime

from django.shortcuts import get_object_or_404, redirect, render
from django.urls import NoReverseMatch, reverse
from django.utils import timezone

from apps.experiences.models import Event

from .models import Destination, Guide, Package, Region


def explore_island(request):
    """Explore the Island page (regions + map)."""
    regions = Region.objects.prefetch_related('destinations')
    destinations = Destination.objects.select_related('region')
    map_points = [
        {'name': d.name, 'region': d.region.name,
         'lat': float(d.latitude), 'lng': float(d.longitude),
         'url': d.get_absolute_url()}
        for d in destinations if d.latitude is not None and d.longitude is not None
    ]
    return render(request, 'destinations/explore_island.html', {
        'regions': regions,
        'map_points': map_points,
    })


def region_detail(request, slug):
    """North / South / East / West / Central pages - ONE template for all five."""
    region = get_object_or_404(Region, slug=slug)
    events = Event.objects.filter(destination__region=region, date__gte=timezone.localdate())[:6]
    return render(request, 'destinations/region_detail.html', {
        'region': region,
        'destinations': region.destinations.all(),
        'events': events,
    })


def destination_detail(request, slug):
    destination = get_object_or_404(Destination.objects.select_related('region'), slug=slug)
    return render(request, 'destinations/destination_detail.html', {
        'destination': destination,
        'events': destination.events.filter(date__gte=timezone.localdate()),
        'packages': destination.packages.all(),
    })


def guides_packages(request):
    """Guides & Packages page."""
    return render(request, 'destinations/guides_packages.html', {
        'guides': Guide.objects.filter(is_active=True),
        'packages': Package.objects.select_related('guide'),
    })


def guide_detail(request, slug):
    """Guide profile page (e.g. Aliyah C., John W.)."""
    guide = get_object_or_404(Guide, slug=slug, is_active=True)
    return render(request, 'destinations/guide_detail.html', {
        'guide': guide,
        'packages': guide.packages.all(),
    })


# =============================================================================
# EXPLORE BOARD (Figma "Explore Board" frame)
#
# This page has its own header/nav-arrows/logo (matches the Figma frame), so it
# does NOT extend base.html. All the cards come from the Python lists below;
# when the team's real models (experiences, bookings, favourites) are ready,
# replace each list with a queryset returning the SAME keys and the template
# keeps working unchanged.
# =============================================================================

# ---------------------------------------------------------------------------
# 1. LINKS TO THE OTHER PAGES
#    key: (url name used by the teammate's urls.py, fallback path)
#    If a teammate's url name is different, change it here only.
# ---------------------------------------------------------------------------
PAGE_URLS = {
    "home":               ("core:home", "/"),
    "explore_island":     ("destinations:explore_island", "/destinations/"),
    "guides_packages":    ("destinations:guides_packages", "/destinations/guides-packages/"),
    "island_calendar":    ("experiences:island_calendar", "/experiences/calendar/"),
    "explore_board":      ("destinations:explore_board", "/destinations/board/"),
    "reserve_experience": ("bookings:reserve_experience", "/bookings/reserve/"),
    "my_experiences":     ("experiences:my_experiences", "/experiences/my-experiences/"),
    "profile":            ("users:profile", "/accounts/profile/"),
    "login":              ("users:login", "/accounts/login/"),
    "logout":             ("users:logout", "/accounts/logout/"),
    "create_account":     ("users:create_account", "/accounts/create-account/"),
    "privacy_policy":     ("privacy_policy", "#"),
    "terms_of_service":   ("terms_of_service", "#"),
    "legal":              ("legal", "#"),
}


def safe_reverse(url_name, fallback="#"):
    try:
        return reverse(url_name)
    except NoReverseMatch:
        return fallback


def build_page_links():
    return {key: safe_reverse(name, fallback) for key, (name, fallback) in PAGE_URLS.items()}


# ---------------------------------------------------------------------------
# 2. NAVIGATION BAR (the arrows scroll through these tabs)
# ---------------------------------------------------------------------------
NAV_ITEMS = [
    ("home", "Discover Mauritius"),
    ("explore_island", "Explore the Island"),
    ("guides_packages", "Guides & Packages"),
    ("island_calendar", "Island Calendar"),
    ("explore_board", "Explore Board"),
    ("reserve_experience", "Reserve Your Experience"),
    ("my_experiences", "My Experiences"),
]


# ---------------------------------------------------------------------------
# 3. PAGE DATA (frame stage - replace with models later, keep the same keys)
#    image = file name inside static/destinations/explore_board/images/
# ---------------------------------------------------------------------------
CATEGORIES = [
    {"name": "Nature", "icon": "🌴"},
    {"name": "Food", "icon": "🍔"},
    {"name": "Culture", "icon": "🌍"},
    {"name": "History", "icon": "🏛️"},
    {"name": "Local Experience", "icon": "🧭"},
]

FAVOURITES = [
    {"slug": "national-history-museum", "title": "National History Museum",
     "category": "History", "rating": 4.2,
     "image": "fav_national_history_museum.jpg", "is_favourite": True},
    {"slug": "7-cascades-hike", "title": "7 Cascades Hike",
     "category": "Nature", "rating": 4.7,
     "image": "seven_cascades.jpg", "is_favourite": False},
    {"slug": "sunset-flic-en-flac", "title": "Sunset at Flic en Flac",
     "category": "Nature", "rating": 4.9,
     "image": "sunset_flic_en_flac.jpg", "is_favourite": True},
    {"slug": "le-morne-brabant", "title": "Le Morne Brabant",
     "category": "Nature", "rating": 4.9,
     "image": "le_morne_brabant.jpg", "is_favourite": True},
    {"slug": "bazaar-port-louis", "title": "Bazaar Port Louis",
     "category": "Culture", "rating": 4.6,
     "image": "bazaar_port_louis.jpg", "is_favourite": True},
    {"slug": "rochester-falls", "title": "Rochester Falls",
     "category": "Nature", "rating": 4.5,
     "image": "rochester_falls.jpg", "is_favourite": False},
]

RECOMMENDED = [
    {"slug": "le-morne-brabant", "title": "Le Morne Brabant",
     "tags": ["Nature", "History"], "rating": 4.9,
     "description": "Hike the iconic Le Morne Brabant and enjoy breathtaking views",
     "price": 1500, "image": "le_morne_brabant.jpg"},
    {"slug": "mauritian-food-journey", "title": "Mauritian Food Journey",
     "tags": ["Food", "Local Experience"], "rating": 4.7,
     "description": "Taste the flavours of Mauritius and savour a delicious journey through its local cuisine",
     "price": 1500, "image": "mauritian_food_journey.jpg"},
    {"slug": "national-history-museum", "title": "National History Museum",
     "tags": ["History", "Culture"], "rating": 4.5,
     "description": "Discover Mauritius' rich history and explore fascinating stories from the island's past",
     "price": None, "image": "national_history_museum.jpg"},
    {"slug": "7-cascades-hike", "title": "7 Cascades Hike",
     "tags": ["Nature"], "rating": 4.7,
     "description": "Trek through lush forest to seven stunning waterfalls and natural pools",
     "price": 1800, "image": "seven_cascades.jpg"},
    {"slug": "street-food-quest-rose-hill", "title": "Street Food Quest",
     "tags": ["Food", "Local Experience"], "rating": 4.8,
     "description": "Taste dholl puri, gateaux piments and more on a guided walk in Rose Hill",
     "price": 900, "image": "street_food_rose_hill.jpg"},
    {"slug": "bazaar-port-louis-tour", "title": "Bazaar Port Louis Tour",
     "tags": ["Culture", "Local Experience"], "rating": 4.6,
     "description": "Explore the colourful Central Market with a local guide in the capital",
     "price": 1200, "image": "bazaar_port_louis.jpg"},
]

UPCOMING_BOOKINGS = [
    {"slug": "bazaar-port-louis-tour", "title": "Bazaar Port Louis Tour", "guide": "Noxie",
     "start": datetime(2026, 8, 31, 10, 0), "status": "Confirmed",
     "image": "bazaar_port_louis.jpg"},
    {"slug": "street-food-quest-rose-hill", "title": "Street Food Quest in Rose Hill", "guide": "Maimisa",
     "start": datetime(2026, 9, 1, 11, 0), "status": "Confirmed",
     "image": "street_food_rose_hill.jpg"},
    {"slug": "pieter-both-hike", "title": "Pieter Both Hike", "guide": "Peso",
     "start": datetime(2026, 9, 3, 9, 0), "status": "Pending",
     "image": "pieter_both_hike.jpg"},
    {"slug": "rochester-falls", "title": "Rochester Fall", "guide": "Ram",
     "start": datetime(2026, 9, 7, 14, 0), "status": "Pending",
     "image": "rochester_falls.jpg"},
    {"slug": "7-cascades-hike", "title": "7 Cascades Hike", "guide": "Ravi",
     "start": datetime(2026, 9, 12, 8, 0), "status": "Pending",
     "image": "seven_cascades.jpg"},
    {"slug": "le-morne-brabant", "title": "Le Morne Brabant Hike", "guide": "Anjali",
     "start": datetime(2026, 9, 15, 7, 30), "status": "Confirmed",
     "image": "le_morne_brabant.jpg"},
]

ITINERARY = [
    {"slug": "mauritian-food-journey", "title": "Food Journey", "start": datetime(2026, 8, 20, 15, 0),
     "icon": "🍔", "colour": "yellow"},
    {"slug": "le-morne-brabant", "title": "Le Morne Hike", "start": datetime(2026, 8, 25, 8, 30),
     "icon": "🌴", "colour": "green"},
    {"slug": "sunset-flic-en-flac", "title": "Sunset at Flic en Flac", "start": datetime(2026, 8, 29, 17, 0),
     "icon": "🌅", "colour": "pink"},
    {"slug": "bazaar-port-louis-tour", "title": "Bazaar Port Louis Tour", "start": datetime(2026, 8, 31, 10, 0),
     "icon": "🛍️", "colour": "blue"},
    {"slug": "street-food-quest-rose-hill", "title": "Street Food Quest", "start": datetime(2026, 9, 1, 11, 0),
     "icon": "🍜", "colour": "yellow"},
    {"slug": "pieter-both-hike", "title": "Pieter Both Hike", "start": datetime(2026, 9, 3, 9, 0),
     "icon": "⛰️", "colour": "green"},
    {"slug": "rochester-falls", "title": "Rochester Fall", "start": datetime(2026, 9, 7, 14, 0),
     "icon": "💧", "colour": "blue"},
]

# How many items each card shows; the rest appear in the "View All" dropdown
SHOW_FIRST = {"favourites": 3, "recommended": 3, "itinerary": 3, "bookings": 4}


# ---------------------------------------------------------------------------
# 4. CUSTOMER ACCOUNT (shown in the profile dropdown)
# ---------------------------------------------------------------------------
def build_account(user):
    """Returns the logged-in user's details, or None if nobody is logged in."""
    if not user.is_authenticated:
        return None

    full_name = user.get_full_name() or user.username
    initials = "".join(part[0] for part in full_name.split()[:2]).upper()

    if user.is_staff:
        role = "Admin"
    elif user.groups.filter(name="Viewer").exists():
        role = "Viewer"
    else:
        role = "Customer"

    return {
        "full_name": full_name,
        "first_name": user.first_name or user.username,
        "username": user.username,
        "email": user.email,
        "initials": initials,
        "role": role,
        "member_since": user.date_joined,
        "bookings_count": len(UPCOMING_BOOKINGS),
        "favourites_count": sum(1 for fav in FAVOURITES if fav["is_favourite"]),
    }


# ---------------------------------------------------------------------------
# 5. THE VIEW
# ---------------------------------------------------------------------------
def _experience_url(page_links, slug):
    return f'{page_links["reserve_experience"]}?experience={slug}'


def explore_board(request):
    page_links = build_page_links()

    # Search box (?q=) and category chips (?category=) filter "Recommended for you"
    search_query = request.GET.get("q", "").strip()
    active_category = request.GET.get("category", "").strip()

    recommended = []
    for item in RECOMMENDED:
        if active_category and active_category not in item["tags"]:
            continue
        if search_query:
            haystack = " ".join([item["title"], item["description"], *item["tags"]]).lower()
            if search_query.lower() not in haystack:
                continue
        recommended.append({
            **item,
            "price_display": f'{item["price"]:,}' if item["price"] else None,
            "url": _experience_url(page_links, item["slug"]),
        })

    # Typed a search? Jump straight to the best-matching experience instead of
    # just filtering the grid. (Category chips still just filter the page.)
    if search_query and recommended:
        return redirect(recommended[0]["url"])

    # give Favourites / Itinerary / Bookings a link to their experience too
    favourites = [{**fav, "url": _experience_url(page_links, fav["slug"])} for fav in FAVOURITES]
    itinerary = [{**stop, "url": _experience_url(page_links, stop["slug"])} for stop in ITINERARY]
    upcoming_bookings = [{**b, "url": _experience_url(page_links, b["slug"])} for b in UPCOMING_BOOKINGS]

    account = build_account(request.user)
    user_display_name = account["first_name"] if account else "Explorer"

    nav_links = [
        {"key": key, "label": label, "url": page_links[key], "is_active": key == "explore_board"}
        for key, label in NAV_ITEMS
    ]

    context = {
        "user_display_name": user_display_name,
        "page_links": page_links,
        "nav_links": nav_links,
        "categories": CATEGORIES,
        "active_category": active_category,
        "search_query": search_query,
        "favourites": favourites,
        "recommended": recommended,
        "upcoming_bookings": upcoming_bookings,
        "itinerary": itinerary,
        "favourites_preview": favourites[:SHOW_FIRST["favourites"]],
        "recommended_preview": recommended[:SHOW_FIRST["recommended"]],
        "bookings_preview": upcoming_bookings[:SHOW_FIRST["bookings"]],
        "itinerary_preview": itinerary[:SHOW_FIRST["itinerary"]],
        "account": account,
    }
    return render(request, "destinations/explore_board.html", context)