from datetime import datetime

from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import NoReverseMatch, reverse
from django.utils import timezone

from apps.bookings.models import Booking
from apps.experiences.models import Category, Event, Favourite

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
# does NOT extend base.html. All the cards now come from the database
# (apps.experiences.Event/Category/Favourite and apps.bookings.Booking).
# =============================================================================

# ---------------------------------------------------------------------------
# 1. LINKS TO THE OTHER PAGES
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

# How many items each card shows; the rest appear in the "View All" dropdown
SHOW_FIRST = {"favourites": 3, "recommended": 3, "itinerary": 3, "bookings": 4}

# Cosmetic colour cycle for the itinerary timeline icons (Booking/Event don't
# store a colour, so we just rotate through these)
ITIN_COLOURS = ["yellow", "green", "pink", "blue"]


# ---------------------------------------------------------------------------
# 3. CUSTOMER ACCOUNT (shown in the profile dropdown)
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
        "bookings_count": Booking.objects.filter(user=user).count(),
        "favourites_count": Favourite.objects.filter(user=user).count(),
    }


# ---------------------------------------------------------------------------
# 4. THE VIEW
# ---------------------------------------------------------------------------
def _experience_url(page_links, slug):
    return f'{page_links["reserve_experience"]}?experience={slug}'


def _price_display(price):
    return None if not price else f'{price:,.0f}'


def explore_board(request):
    page_links = build_page_links()

    # Search box (?q=) and category chips (?category=) filter "Recommended for you"
    search_query = request.GET.get("q", "").strip()
    active_category = request.GET.get("category", "").strip()

    events = Event.objects.select_related("category").filter(date__gte=timezone.localdate())
    if active_category:
        events = events.filter(category__name=active_category)
    if search_query:
        events = events.filter(
            Q(title__icontains=search_query)
            | Q(short_description__icontains=search_query)
            | Q(description__icontains=search_query)
        )
    events = events.order_by("-rating", "date")

    recommended = [{
        "slug": e.slug,
        "title": e.title,
        "category": e.category.name if e.category else "",
        "rating": e.rating,
        "description": e.short_description or e.description,
        "price_display": _price_display(e.price),
        "image": e.image,
        "url": _experience_url(page_links, e.slug),
    } for e in events]

    # Typed a search? Jump straight to the best-matching experience instead of
    # just filtering the grid. (Category chips still just filter the page.)
    if search_query and recommended:
        return redirect(recommended[0]["url"])

    # ---- Your Favourites (per logged-in user) ----
    if request.user.is_authenticated:
        fav_events = Event.objects.select_related("category").filter(favourited_by__user=request.user)
    else:
        fav_events = Event.objects.none()

    favourites = [{
        "slug": e.slug,
        "title": e.title,
        "category": e.category.name if e.category else "",
        "rating": e.rating,
        "image": e.image,
        "is_favourite": True,
        "url": _experience_url(page_links, e.slug),
    } for e in fav_events]

    # ---- Upcoming Bookings (per logged-in user) ----
    if request.user.is_authenticated:
        booking_qs = (Booking.objects.select_related("event", "event__category")
                      .filter(user=request.user, event__date__gte=timezone.localdate())
                      .exclude(status=Booking.Status.CANCELLED)
                      .order_by("event__date", "event__start_time"))
    else:
        booking_qs = Booking.objects.none()

    upcoming_bookings = [{
        "slug": b.event.slug,
        "title": b.event.title,
        "status": b.get_status_display(),
        "status_class": b.status,
        "start": datetime.combine(b.event.date, b.event.start_time or datetime.min.time()),
        "image": b.event.image,
        "url": _experience_url(page_links, b.event.slug),
    } for b in booking_qs]

    # ---- Your Trip Itinerary (derived from the same bookings) ----
    itinerary = [{
        "slug": b["slug"],
        "title": b["title"],
        "start": b["start"],
        "icon": Event.objects.filter(slug=b["slug"]).values_list("category__icon", flat=True).first() or "📍",
        "colour": ITIN_COLOURS[i % len(ITIN_COLOURS)],
        "url": b["url"],
    } for i, b in enumerate(upcoming_bookings)]

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
        "categories": Category.objects.all(),
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