import math
from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation
from types import SimpleNamespace

from django.db.models import Prefetch, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import NoReverseMatch, reverse

from django.utils import timezone
from django.views.decorators.http import require_POST

from apps.bookings.models import Booking
from apps.experiences.models import Category, Event, Favourite

from .forms import SuggestionForm
from .models import Destination, Guide, HeroTile, Package, Region, WayToExplore


def _regions_with_places():
    """Every region with its places (A-Z) already loaded - used by several pages."""
    return Region.objects.prefetch_related(
        Prefetch('destinations', queryset=Destination.objects.order_by('name')))


def _event_duration_hours(event):
    if not event.start_time or not event.end_time:
        return None
    start = datetime.combine(event.date, event.start_time)
    end = datetime.combine(event.date, event.end_time)
    if end <= start:
        end += timedelta(days=1)
    return math.ceil((end - start).total_seconds() / 3600)


def explore_island(request):
    """Explore the Island page: hero, ways to explore, regions, map, suggestions."""
    regions = list(_regions_with_places())
    ways = list(WayToExplore.objects.all())

    # "Find things to do": places first (grouped by region), then regions, then ways to explore
    search_items = (
        [{'kind': 'place', 'name': d.name, 'note': d.note, 'url': d.region_url,
          'region': r.list_title or r.name, 'keys': f'{d.note} {d.keywords} {d.area} {r.name}'}
         for r in regions for d in r.destinations.all()]
        + [{'kind': 'region', 'name': r.name, 'url': r.get_absolute_url(), 'keys': r.keywords}
           for r in regions]
        + [{'kind': 'way', 'name': w.title, 'url': w.url, 'keys': w.keywords} for w in ways]
    )

    return render(request, 'destinations/explore_island.html', {
        'hero_tiles': HeroTile.objects.all(),
        'ways': ways,
        'regions': regions,
        'search_items': search_items,
    })


@require_POST
def send_suggestion(request):
    """"Suggest an idea" pop-up: saves into Suggestion (read it in /admin/) and answers in JSON."""
    form = SuggestionForm(request.POST)
    if form.is_valid():
        form.save()
        return JsonResponse({'ok': True})
    if 'email' in form.errors:
        error = "That email doesn't look complete. Use a full address like name@gmail.com, or leave it empty."
    else:
        error = 'Please write your idea before sending.'
    return JsonResponse({'ok': False, 'error': error}, status=400)


def island_map(request):
    """Google Map frame (teammate). Every place with latitude/longitude is sent as map_points."""
    places = Destination.objects.select_related('region').exclude(latitude=None).exclude(longitude=None)
    map_points = [{
        'name': d.name, 'region': d.region.name, 'note': d.note,
        'lat': float(d.latitude), 'lng': float(d.longitude),
        'url': d.region_url, 'image': d.image.url if d.image else '',
    } for d in places]
    return render(request, 'destinations/map.html', {
        'regions': Region.objects.all(),
        'map_points': map_points,
        'durations': [
            ('under-2', 'Up to 2 hours'),
            ('2-4', '2–4 hours'),
            ('4-6', '4–6 hours'),
            ('full-day', 'Full day'),
        ],
        'difficulties': Event.DIFFICULTY_CHOICES,
    })


def explore_your_way(request):
    """Browse local experiences from the shared events database."""
    today = timezone.localdate()
    query = request.GET.get('q', '').strip()[:100]
    selected_category = request.GET.get('category', '').strip()
    experiences = Event.objects.filter(date__gte=today).select_related(
        'category', 'destination', 'destination__region'
    )

    if query:
        experiences = experiences.filter(
            Q(title__icontains=query)
            | Q(short_description__icontains=query)
            | Q(description__icontains=query)
            | Q(location_name__icontains=query)
            | Q(destination__name__icontains=query)
            | Q(destination__region__name__icontains=query)
            | Q(category__name__icontains=query)
        )
    if selected_category:
        experiences = experiences.filter(category__slug=selected_category)

    cards = []
    for event in experiences:
        destination = event.destination
        duration_hours = _event_duration_hours(event)
        if duration_hours is None:
            duration_label = 'Duration to be confirmed'
        elif duration_hours <= 1:
            duration_label = '1 hour'
        elif duration_hours <= 3:
            duration_label = f'{duration_hours - 1}-{duration_hours} hours'
        elif duration_hours < 7:
            duration_label = 'Half day'
        else:
            duration_label = 'Full day'

        image = event.image or (destination.image if destination else None)
        try:
            image_url = image.url if image else ''
        except ValueError:
            image_url = ''

        cards.append({
            'event': event,
            'location': event.location_name or (
                f'{destination.name}, {destination.region.name}' if destination else 'Mauritius'
            ),
            'duration': duration_label,
            'image_url': image_url,
        })

    hero_card = next((card for card in cards if card['image_url']), None)
    categories = Category.objects.filter(events__date__gte=today).distinct()

    return render(request, 'destinations/explore_your_way.html', {
        'cards': cards,
        'categories': categories,
        'query': query,
        'selected_category': selected_category,
        'hero_image_url': hero_card['image_url'] if hero_card else '',
    })


def region_detail(request, slug):
    """North / South / East / West / Central frames (teammates) - ONE template for all five.
    ?place=<slug> tells which place was clicked on Explore the Island."""
    region = get_object_or_404(Region, slug=slug)
    destinations = region.destinations.all()
    packages = (
        Package.objects.filter(destinations__region=region)
        .select_related('guide')
        .prefetch_related('destinations')
        .distinct()
    )
    guides = (
        Guide.objects.filter(is_active=True, packages__destinations__region=region)
        .distinct()
    )
    events = (
        Event.objects.filter(destination__region=region, date__gte=timezone.localdate())
        .select_related('category', 'destination')
    )
    return render(request, 'destinations/region_detail.html', {
        'region': region,
        'destinations': region.destinations.order_by('name'),
        'selected_place': request.GET.get('place', ''),
        'packages': packages,
        'guides': guides,
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
    """Guides & Packages page, optionally scoped to a region."""
    region_slug = request.GET.get('region', '').strip()
    region = get_object_or_404(Region, slug=region_slug) if region_slug else None
    guides = Guide.objects.filter(is_active=True)
    packages = Package.objects.select_related('guide')
    if region:
        guides = guides.filter(packages__destinations__region=region).distinct()
        packages = packages.filter(destinations__region=region).distinct()
    return render(request, 'destinations/guides_packages.html', {
        'region': region,
        'guides': guides,
        'packages': packages,
    })


def guide_detail(request, slug):
    guide = get_object_or_404(Guide, slug=slug, is_active=True)
    return render(request, 'destinations/guide_detail.html', {
        'guide': guide,
        'packages': guide.packages.all(),
        'reviews': guide.reviews.all()[:6],
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

    if request.user.is_authenticated:
        favourite_event_ids = set(
            Favourite.objects.filter(user=request.user).values_list("event_id", flat=True)
        )
    else:
        favourite_event_ids = set()

    recommended = [{
        "slug": e.slug,
        "title": e.title,
        "category": e.category.name if e.category else "",
        "rating": e.rating,
        "description": e.short_description or e.description,
        "price_display": _price_display(e.price),
        "image": e.image,
        "url": _experience_url(page_links, e.slug),
        "is_favourite": e.id in favourite_event_ids,
        "toggle_url": reverse("experiences:toggle_favourite_by_slug", args=[e.slug]),
    } for e in events]

    if search_query and recommended:
        return redirect(recommended[0]["url"])

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
        "toggle_url": reverse("experiences:toggle_favourite_by_slug", args=[e.slug]),
    } for e in fav_events]

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
        # These three are landing-page categories, not filter chips for this board.
        "categories": Category.objects.exclude(slug__in=("nature", "history", "local_experience")),
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


def reserve_experience(request):
    """Placeholder - real page not merged into main yet."""
    raise Http404("This page is not available yet.")

def experience_finder(request):
    """Filter and display bookable experiences from the shared events database."""
    today = timezone.localdate()
    query = request.GET.get('q', '').strip()[:100]
    location_query = request.GET.get('location', '').strip()[:100]
    selected_category = request.GET.get('category', '')
    selected_region = request.GET.get('region', '')
    selected_sort = request.GET.get('sort', 'recommended')
    selected_difficulty = request.GET.get('difficulty', '')
    selected_durations = [duration for duration in request.GET.getlist('duration') if duration]
    minimum_price_input = request.GET.get('min_price', '0').strip()
    maximum_price_input = request.GET.get('max_price', '10000').strip()
    filter_errors = []

    categories = list(Category.objects.all())
    if not categories:
        categories = [
            SimpleNamespace(name='Nature', slug='nature', icon='♧'),
            SimpleNamespace(name='Culture', slug='culture', icon='🏛'),
            SimpleNamespace(name='Heritage and History', slug='heritage-history', icon='♜'),
            SimpleNamespace(name='Food and Drinks', slug='food-drinks', icon='♜'),
            SimpleNamespace(name='Local Experiences', slug='local-experiences', icon='♟'),
        ]
    regions = Region.objects.all()
    valid_categories = {category.slug for category in categories}
    valid_regions = set(regions.values_list('slug', flat=True))
    if selected_category and selected_category not in valid_categories:
        filter_errors.append('Choose a valid activity category.')
        selected_category = ''
    if selected_region and selected_region not in valid_regions:
        filter_errors.append('Choose a valid island location.')
        selected_region = ''
    valid_difficulties = {choice[0] for choice in Event.DIFFICULTY_CHOICES}
    if selected_difficulty and selected_difficulty not in valid_difficulties:
        filter_errors.append('Choose a valid difficulty level.')
        selected_difficulty = ''
    valid_durations = {'under-2', '2-4', '4-6', 'full-day'}
    if any(duration not in valid_durations for duration in selected_durations):
        filter_errors.append('Choose a valid experience duration.')
        selected_durations = [duration for duration in selected_durations if duration in valid_durations]
    if selected_sort not in {'recommended', 'date', 'price_low', 'price_high', 'name'}:
        filter_errors.append('Choose a valid sort order.')
        selected_sort = 'recommended'

    def parse_price(value, label):
        if not value:
            return None
        try:
            price = Decimal(value)
        except InvalidOperation:
            filter_errors.append(f'Enter a valid {label} price.')
            return None
        if not price.is_finite() or price < 0:
            filter_errors.append(f'{label.capitalize()} price must be zero or more.')
            return None
        return price

    minimum_price = parse_price(minimum_price_input, 'minimum') or Decimal('0')
    maximum_price = parse_price(maximum_price_input, 'maximum')
    if maximum_price == Decimal('10000'):
        maximum_price = None
    if minimum_price is not None and maximum_price is not None and minimum_price > maximum_price:
        filter_errors.append('Minimum price cannot be greater than maximum price.')
        minimum_price = maximum_price = None

    experiences = Event.objects.filter(date__gte=today).select_related(
        'category', 'destination', 'destination__region'
    )
    if query:
        experiences = experiences.filter(
            Q(title__icontains=query)
            | Q(short_description__icontains=query)
            | Q(description__icontains=query)
            | Q(location_name__icontains=query)
            | Q(destination__name__icontains=query)
            | Q(destination__region__name__icontains=query)
            | Q(category__name__icontains=query)
        )
    if location_query:
        experiences = experiences.filter(
            Q(location_name__icontains=location_query)
            | Q(destination__name__icontains=location_query)
            | Q(destination__region__name__icontains=location_query)
        )
    if selected_category:
        experiences = experiences.filter(category__slug=selected_category)
    if selected_region:
        experiences = experiences.filter(destination__region__slug=selected_region)
    if minimum_price:
        experiences = experiences.filter(price__gte=minimum_price)
    if maximum_price is not None:
        experiences = experiences.filter(price__lte=maximum_price)
    if selected_difficulty:
        experiences = experiences.filter(difficulty=selected_difficulty)
    if selected_durations:
        matching_event_ids = []
        for event in experiences:
            duration_hours = _event_duration_hours(event)
            if duration_hours is None:
                continue
            if (
                ('under-2' in selected_durations and duration_hours <= 2)
                or ('2-4' in selected_durations and 2 < duration_hours <= 4)
                or ('4-6' in selected_durations and 4 < duration_hours <= 6)
                or ('full-day' in selected_durations and duration_hours >= 7)
            ):
                matching_event_ids.append(event.pk)
        experiences = experiences.filter(pk__in=matching_event_ids)

    results = []
    for event in experiences:
        destination = event.destination
        duration_hours = _event_duration_hours(event)
        if duration_hours:
            duration_label = 'Full day' if duration_hours >= 7 else (
                f'{duration_hours} hour' if duration_hours == 1 else f'{duration_hours} hours'
            )
        else:
            duration_label = 'Duration to be confirmed'
        results.append({
            'id': f'experience-{event.pk}',
            'name': event.title,
            'description': event.short_description or event.description,
            'location': event.location_name or (
                f'{destination.name}, {destination.region.name}' if destination else 'Mauritius'
            ),
            'location_url': destination.get_absolute_url() if destination else '',
            'category': event.category,
            'category_name': event.category.name if event.category else 'Experience',
            'difficulty': event.get_difficulty_display() if event.difficulty else '',
            'duration': duration_label,
            'price': event.price,
            'date': event.date,
            'is_featured': event.is_featured,
            'url': event.get_absolute_url(),
            'image_url': event.image.url if event.image else '',
            'lat': float(destination.latitude) if destination and destination.latitude is not None else None,
            'lng': float(destination.longitude) if destination and destination.longitude is not None else None,
            'map_region': destination.region.name if destination else event.location_name,
        })

    if selected_sort == 'name':
        results.sort(key=lambda result: result['name'].casefold())
    elif selected_sort == 'price_low':
        results.sort(key=lambda result: (
            result['price'] is None,
            result['price'] if result['price'] is not None else Decimal('Infinity'),
        ))
    elif selected_sort == 'price_high':
        results.sort(key=lambda result: (
            result['price'] is None,
            -(result['price'] or Decimal('0')),
        ))
    elif selected_sort == 'date':
        results.sort(key=lambda result: result['date'])
    elif selected_sort == 'recommended':
        results.sort(key=lambda result: (
            not result['is_featured'],
            result['date'],
            result['name'].casefold(),
        ))

    map_points = []
    located_points = [result for result in results if result['lat'] is not None and result['lng'] is not None]
    for result in located_points:
        overlap_offset = (len(map_points) % 3 - 1) * 1.1
        result['map_x'] = max(4, min(96, 15 + (result['lng'] - 57.28) / 0.54 * 69 + overlap_offset))
        result['map_y'] = max(4, min(96, 7 + (-19.97 - result['lat']) / 0.56 * 83 + overlap_offset))
        map_points.append(result)

    return render(request, 'destinations/experience_finder.html', {
        'results': results,
        'result_count': len(results),
        'categories': categories,
        'regions': regions,
        'query': query,
        'location_query': location_query,
        'selected_category': selected_category,
        'selected_region': selected_region,
        'selected_sort': selected_sort,
        'selected_difficulty': selected_difficulty,
        'selected_durations': selected_durations,
        'minimum_price_input': minimum_price_input,
        'maximum_price_input': maximum_price_input,
        'filter_errors': filter_errors,
        'map_points': map_points,
        'durations': [
            ('under-2', 'Up to 2 hours'),
            ('2-4', '2–4 hours'),
            ('4-6', '4–6 hours'),
            ('full-day', 'Full day'),
        ],
        'difficulties': Event.DIFFICULTY_CHOICES,
    })