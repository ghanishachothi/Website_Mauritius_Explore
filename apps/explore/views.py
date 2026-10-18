import json
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.templatetags.static import static
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST
from .models import Destination
from .models import Event
from .forms import ContactForm, WaitlistForm
from .models import AppWaitlist, MonthTip, SitePage
from django.contrib import messages
from django.contrib.auth import login, update_session_auth_hash, get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import views as auth_views
from django.contrib.auth.tokens import default_token_generator
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from .forms import CustomPasswordResetForm, ProfileForm, SignUpForm, UserUpdateForm
from .models import Profile
import math
from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation
from types import SimpleNamespace
from django.db.models import Prefetch, Q
from django.http import JsonResponse
from django.urls import NoReverseMatch, reverse
from .models import Booking
from .models import Category, Event, Favourite
from .forms import SuggestionForm
from .models import Destination, Guide, HeroTile, Package, Region, WayToExplore
import calendar
from datetime import date, time as time_min, timedelta
from django.core.exceptions import PermissionDenied
from django.db.models import Q
import uuid
from .models import Region
from .models import Category, ChatMessage, ChatSession, Event, Experience, FAQEntry, Review, Favourite
from django.http import Http404
from .models import Package
from .forms import CheckoutForm, ReserveForm, ReservePackageForm
from .models import Booking, Payment
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Sum
from django.shortcuts import render


# ======================================================================
# from the old "core" app
# ======================================================================

# Apps talk to each other just by importing each other's models:



def home(request):
    """Discover Mauritius homepage: hero, search, "When to come" and Top Destinations."""
    # --- Top Destinations carousel (featured places first) ---
    destinations = []
    for place in Destination.objects.select_related('region').filter(is_featured=True).order_by('order', 'name')[:12]:
        destinations.append({
            'name': place.name,
            'area': place.area or place.region.name,
            'url': place.get_absolute_url(),
            'image_url': place.image.url if place.image else static('images/combined-image__3_.jpg'),
        })

    # --- "When to come" planner ---
    tips = list(MonthTip.objects.all())
    months = [{'month': t.month, 'short_name': t.short_name} for t in tips]
    month_data = [{
        'month': t.month, 'name': t.name, 'headline': t.headline,
        'air': t.air, 'sea': t.sea, 'crowd': t.crowd,
        'note': t.note, 'highlight': t.highlight,
    } for t in tips]

    # --- what the search bar can find: the site's pages only ---
    # (places and events are found with the search on Explore the Island)
    search_items = []
    seen_urls = set()
    for page in SitePage.objects.filter(frame_ready=True):
        if page.url in seen_urls:        # two pages with the same address show once
            continue
        seen_urls.add(page.url)
        search_items.append({
            'group': 'Pages', 'kind': 'page', 'name': page.name,
            'note': '', 'url': page.url, 'keys': page.keywords,
        })

    return render(request, 'core/home.html', {
        'destinations': destinations,
        'months': months,
        'month_data': month_data,
        'search_items': search_items,
        'calendar_url': reverse('experiences:island_calendar'),
    })


@require_POST
def contact(request):
    """Help & Contact pop-up. Saves into ContactMessage and answers in JSON."""
    form = ContactForm(request.POST)
    if form.is_valid():
        form.save()
        return JsonResponse({'ok': True})
    return JsonResponse({'ok': False, 'error': 'Please fill in your name, a valid email and your message.'})


@require_POST
def app_waitlist(request):
    """"Notify me" in the app panel. Saves into AppWaitlist and answers in JSON."""
    form = WaitlistForm(request.POST)
    if form.is_valid():
        AppWaitlist.objects.get_or_create(email=form.cleaned_data['email'],
                                          store=form.cleaned_data['store'] or 'any')
        return JsonResponse({'ok': True})
    return JsonResponse({'ok': False, 'error': 'Please enter a valid email address.'})


def manifest(request):
    """Lets phones install the site like an app (Add to Home Screen)."""
    data = {
        'name': 'Mauritius Explorer',
        'short_name': 'Mauritius',
        'start_url': '/',
        'scope': '/',
        'display': 'standalone',
        'background_color': '#ffffff',
        'theme_color': '#10276B',
        'icons': [{'src': static('images/app/icon-192.png'), 'sizes': '192x192', 'type': 'image/png'}],
    }
    return HttpResponse(json.dumps(data), content_type='application/manifest+json')


SERVICE_WORKER_JS = """
// Minimal service worker: needed so browsers offer "Add to home screen".
self.addEventListener('install', () => self.skipWaiting());
self.addEventListener('activate', event => event.waitUntil(self.clients.claim()));
self.addEventListener('fetch', () => {});
"""


def service_worker(request):
    response = HttpResponse(SERVICE_WORKER_JS, content_type='application/javascript')
    response['Service-Worker-Allowed'] = '/'
    return response


def contact_page(request):
    """Old /contact/ links: open the homepage with the Help pop-up."""
    return redirect(reverse('core:home') + '#help')


# ======================================================================
# from the old "users" app
# ======================================================================

User = get_user_model()


def signup(request):
    """Create Account page."""
    if request.user.is_authenticated:
        return redirect('users:profile')

    form = SignUpForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save()

        # Log user in
        login(request, user, backend='django.contrib.auth.backends.ModelBackend')

        display_name = user.first_name if user.first_name else user.username
        messages.success(request, f'Welcome to Mauritius Explore, {display_name}!')
        return redirect('users:profile')

    return render(request, 'users/signup.html', {'form': form})


@login_required
def profile(request):
    """Profile page (view + edit). Full access for standard users and admins."""
    profile_obj, _ = Profile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        user = request.user

        # Save User model fields
        full_name = request.POST.get('full_name', '').strip()
        if full_name:
            name_parts = full_name.split(' ', 1)
            user.first_name = name_parts[0]
            user.last_name = name_parts[1] if len(name_parts) > 1 else ''

        user.username = request.POST.get('username', user.username)
        user.email = request.POST.get('email', user.email)
        user.save()

        # Check and handle uploaded avatar file
        if 'avatar' in request.FILES:
            profile_obj.avatar = request.FILES['avatar']

        # Save Profile model fields
        profile_obj.gender = request.POST.get('gender', profile_obj.gender)
        profile_obj.language = request.POST.get('language', profile_obj.language)
        profile_obj.phone_number = request.POST.get('phone_number', profile_obj.phone_number)
        profile_obj.nationality = request.POST.get('nationality', profile_obj.nationality)
        profile_obj.save()

        messages.success(request, 'Profile updated successfully!')
        return redirect('users:profile')

    return render(request, 'users/profile.html', {
        'profile': profile_obj,
    })


@login_required
def change_password(request):
    """Securely handle user password change."""
    if request.method == 'POST':
        form = PasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            user = form.save()
            # Keeps the user logged in after password change
            update_session_auth_hash(request, user)
            messages.success(request, 'Your password was successfully updated!')
        else:
            for error_list in form.errors.values():
                for error in error_list:
                    messages.error(request, error)

    return redirect('users:profile')


@login_required
def request_delete_account(request):
    """
    Handle account deletion:
    - If user is Admin/Staff: Instantly deletes the account.
    - If user is Regular User: Sets deletion_requested flag for admin approval.
    """
    if request.method == 'POST':
        user = request.user

        # Full access override for Admin/Staff
        if user.is_staff or user.is_superuser:
            user.delete()
            messages.success(request, 'Account successfully deleted by admin.')
            return redirect('users:signup')

        # Standard workflow for regular users
        profile_obj, _ = Profile.objects.get_or_create(user=user)
        profile_obj.deletion_requested = True
        profile_obj.save()
        messages.info(request, 'Your account deletion request has been submitted to an administrator for approval.')

    return redirect('users:profile')


class DevPasswordResetView(auth_views.PasswordResetView):
    """
    Development Password Reset View: Bypasses email sending and terminal line-wrapping issues
    by redirecting directly to the reset confirmation page upon valid email submission.
    """
    template_name = 'users/password_reset.html'
    form_class = CustomPasswordResetForm

    def form_valid(self, form):
        email = form.cleaned_data["email"]
        associated_users = User.objects.filter(email__iexact=email)

        if associated_users.exists():
            for user in associated_users:
                uid = urlsafe_base64_encode(force_bytes(user.pk))
                token = default_token_generator.make_token(user)
                return redirect(reverse('users:password_reset_confirm', kwargs={'uidb64': uid, 'token': token}))

        return super().form_valid(form)


# ======================================================================
# from the old "destinations" app
# ======================================================================

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


@login_required
def destinations_explore_your_way(request):
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
    # clicking an experience opens its detail page
    return reverse("experiences:event_detail", args=[slug])
def _price_display(price):
    return None if not price else f'{price:,.0f}'

@login_required
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
        "reserve_url": reverse("bookings:reserve", args=[e.slug]),
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
        "reserve_url": reverse("bookings:reserve", args=[e.slug]),
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


def destinations_reserve_experience(request):
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


# ======================================================================
# from the old "experiences" app
# ======================================================================

EXPLORE_YOUR_WAY_CATEGORY_SLUGS = (
    'nature',
    'culture',
    'heritage-and-history',
    'food-and-drinks',
    'local-experiences',
)


def all_events(request, *, page_title='All Events & Activities'):
    """All Events & Activities page. Filter: ?category=hiking  Search: ?q=kayak"""
    query = request.GET.get('q', '').strip()

    selected = request.GET.get('category')

    events = (Event.objects
          .filter(date__gte=timezone.localdate(), show_on_calendar=False)
          .select_related('category', 'destination'))


    if query:
        events = events.filter(
            Q(title__icontains=query)
            | Q(location_name__icontains=query)
            | Q(short_description__icontains=query)
            | Q(category__name__icontains=query)
        )

    if selected:
        events = events.filter(category__slug=selected)

    return render(request, 'experiences/all_events.html', {
        'events': events,
        'categories': Category.objects.filter(events__show_on_calendar=False).distinct(),
        'selected_category': selected,
        'query': query,
        'page_title': page_title,
    })


def experience_category(request, category_slug):
    """A single category's events, e.g. /experiences/category/hiking/"""
    category = get_object_or_404(Category, slug=category_slug)
    events = (Event.objects.filter(date__gte=timezone.localdate(), category=category)
              .select_related('category', 'destination'))
    return render(request, 'experiences/all_events.html', {
        'events': events,
        'categories': Category.objects.all(),
        'selected_category': category_slug,
    })


def experience_insight(request):
    event = get_object_or_404(Event, slug='ile-aux-cerfs-catamaran-day')
    return event_detail(request, event.slug)

@login_required
def explore_your_way(request):
    """Explore Your Way page: search + filters, matching the Figma design."""
    today = timezone.localdate()
    events = Event.objects.filter(date__gte=today).select_related(
        'category', 'destination', 'destination__region'
    )
    query = request.GET.get('q', '').strip()
    where = request.GET.get('where', '').strip()
    selected_category = request.GET.get('category', '').strip()
    selected_location = request.GET.get('location', '').strip()
    selected_duration = request.GET.get('duration', '').strip()
    min_price = request.GET.get('min_price', '').strip()
    max_price = request.GET.get('max_price', '').strip()
    selected_difficulty = request.GET.get('difficulty', '').strip()
    sort = request.GET.get('sort', 'popular').strip() or 'popular'

    if query:
        events = events.filter(
            Q(title__icontains=query)
            | Q(short_description__icontains=query)
            | Q(description__icontains=query)
            | Q(category__name__icontains=query)
            | Q(destination__name__icontains=query)
        )
    if where:
        events = events.filter(
            Q(destination__name__icontains=where)
            | Q(destination__region__name__icontains=where)
            | Q(location_name__icontains=where)
        )
    if selected_category:
        events = events.filter(category__slug=selected_category)
    if selected_location:
        events = events.filter(destination__region__name__iexact=selected_location)
    if selected_duration == 'short':
        events = events.filter(start_time__isnull=False, end_time__isnull=False)
        events = [e for e in events if 0 < (e.end_time.hour * 60 + e.end_time.minute) - (e.start_time.hour * 60 + e.start_time.minute) <= 120]
    elif selected_duration == 'half':
        events = events.filter(start_time__isnull=False, end_time__isnull=False)
        events = [e for e in events if 120 < (e.end_time.hour * 60 + e.end_time.minute) - (e.start_time.hour * 60 + e.start_time.minute) <= 240]
    elif selected_duration == 'full':
        events = events.filter(start_time__isnull=False, end_time__isnull=False)
        events = [e for e in events if (e.end_time.hour * 60 + e.end_time.minute) - (e.start_time.hour * 60 + e.start_time.minute) > 240]
    if min_price:
        try:
            events = events.filter(price__gte=float(min_price))
        except ValueError:
            pass
    if max_price:
        try:
            events = events.filter(price__lte=float(max_price))
        except ValueError:
            pass
    if selected_difficulty:
        events = events.filter(difficulty=selected_difficulty)

    if sort == 'price_low':
        events = sorted(events, key=lambda e: e.price)
    elif sort == 'price_high':
        events = sorted(events, key=lambda e: e.price, reverse=True)
    elif sort == 'rating':
        events = sorted(events, key=lambda e: e.rating, reverse=True)
    elif sort == 'date':
        events = sorted(events, key=lambda e: (e.date, e.start_time or time_min(0, 0)))
    else:  # popular
        events = sorted(events, key=lambda e: e.review_count, reverse=True)

    locations = (
        Region.objects.order_by('order', 'name')
    )

    # Filters carried across when one dropdown changes
    preserved_filters = []
    for key in ('q', 'where', 'category', 'location', 'duration', 'max_price', 'difficulty', 'sort'):
        value = {'q': query, 'where': where, 'category': selected_category, 'location': selected_location,
                 'duration': selected_duration, 'max_price': max_price, 'difficulty': selected_difficulty,
                 'sort': sort}.get(key, '')
        if value:
            preserved_filters.append((key, value))

    return render(request, 'experiences/explore_your_way.html', {
        'events': events,
        'event_count': len(events),
        'categories': sorted(
            Category.objects.filter(slug__in=EXPLORE_YOUR_WAY_CATEGORY_SLUGS),
            key=lambda category: EXPLORE_YOUR_WAY_CATEGORY_SLUGS.index(category.slug),
        ),
        'locations': locations,
        'query': query,
        'where': where,
        'selected_category': selected_category,
        'selected_location': selected_location,
        'selected_duration': selected_duration,
        'min_price': min_price,
        'max_price': max_price,
        'selected_difficulty': selected_difficulty,
        'sort': sort,
        'preserved_filters': preserved_filters,
    })


def event_detail(request, slug):
    event = get_object_or_404(
        Event.objects.select_related('category', 'destination', 'guide', 'destination__region'),
        slug=slug,
    )
    reviews = list(event.reviews.select_related('user').all())
    if reviews:
        review_count_label = f'{len(reviews)}'
    else:
        review_count_label = f'{event.review_count}'

    is_favourited = False
    if request.user.is_authenticated:
        is_favourited = Favourite.objects.filter(user=request.user, event=event).exists()
    if request.method == 'POST' and request.POST.get('action') == 'toggle-favourite':
        if not request.user.is_authenticated:
            return redirect(f"{reverse('users:login')}?next={request.path}")
        favourite, created = Favourite.objects.get_or_create(user=request.user, event=event)
        if not created:
            favourite.delete()
            is_favourited = False
        else:
            is_favourited = True
        return redirect(request.path)

    gallery_images = []
    for f in [event.image, event.gallery_image_1, event.gallery_image_2, event.gallery_image_3]:
        if f:
            try:
                gallery_images.append(f.url)
            except ValueError:
                pass

    primary_image = gallery_images[0] if gallery_images else None
    thumbnail_images = gallery_images[1:4]

    inclusions_list = event.get_inclusions_list()
    itinerary_rows = event.get_itinerary_rows()

    languages_label = event.get_languages_display_label()
    cancellation_label = event.get_cancellation_label()
    group_label = event.get_group_size_label()
    pickup_label = (
        event.pickup_details.replace('\r\n', '\n') if event.pickup_details else ''
    )
    duration_label = event.get_duration_label()

    difficulty_label = event.get_difficulty_display() or 'Any Level'
    region_label = ''
    if event.destination and event.destination.region:
        region_label = f'{event.destination.region}, Mauritius'
    elif event.destination:
        region_label = f'{event.destination.name}, Mauritius'
    elif event.location_name:
        region_label = event.location_name

    if event.premium_price is not None and event.premium_price > 0:
        premium_price = event.premium_price
    else:
        premium_price = None
    standard_price = event.price

    standard_package_label = event.standard_package_label or 'Standard package'
    premium_package_label = event.premium_package_label or 'Premium package'

    guide = event.guide
    if guide:
        guide_rating = float(guide.rating) if guide.rating is not None else 4.5
    else:
        guide_rating = None

    related_events = list(
        Event.objects
        .filter(date__gte=timezone.localdate())
        .filter(Q(destination=event.destination) | Q(category=event.category))
        .exclude(pk=event.pk)
        .select_related('category', 'destination')
        .order_by('date')[:4]
    )

    min_price = standard_price
    max_price = standard_price
    if premium_price:
        max_price = premium_price

    if min_price == 0:
        price_display = 'Free'
    elif min_price == max_price:
        price_display = f'Rs {min_price:,.0f}'
    else:
        price_display = f'Rs {min_price:,.0f} – Rs {max_price:,.0f}'

    breadcrumbs = [
        ('Home', reverse('core:home')),
        ('Experiences', reverse('experiences:all_events')),
        ('All Experiences', reverse('experiences:explore_your_way')),
        (event.title, None),
    ]

    return render(request, 'experiences/event_detail.html', {
        'event': event,
        'reviews': reviews,
        'is_favourited': is_favourited,
        'breadcrumbs': breadcrumbs,
        'breadcrumb_title': event.title,
        'primary_image': primary_image,
        'thumbnail_images': thumbnail_images,
        'gallery_images': gallery_images,
        'gallery_count': len(gallery_images),
        'inclusions_list': inclusions_list,
        'itinerary_rows': itinerary_rows,
        'languages_label': languages_label,
        'cancellation_label': cancellation_label,
        'group_label': group_label,
        'pickup_label': pickup_label,
        'duration_label': duration_label,
        'difficulty_label': difficulty_label,
        'region_label': region_label,
        'standard_price': standard_price,
        'premium_price': premium_price,
        'standard_package_label': standard_package_label,
        'premium_package_label': premium_package_label,
        'guide': guide,
        'guide_rating': guide_rating,
        'related_events': related_events,
        'price_display': price_display,
        'reserve_url': reverse('bookings:reserve', args=[event.slug]),
        'rating_label': f'{float(event.rating):.1f}',
        'review_count_label': review_count_label,
    })

# "Any date" dropdown
WHEN_CHOICES = [
    ('any', 'Any date'),
    ('today', 'Today'),
    ('weekend', 'This weekend'),
    ('month', 'This month'),
]

# The six "What to expect" tiles: category slug -> picture in static/images/
# A tile whose category does not exist yet is simply skipped.
EXPECT_TILES = [
    ('food-street-eats', 'Food &<br>Street Eats', 'images/island-calendar/Food.png'),
    ('nightlife-parties', 'Nightlife &<br>Parties', 'images/island-calendar/Nightlife.png'),
    ('nature-outdoor', 'Nature &<br>Outdoor', 'images/island-calendar/Nature.png'),
    ('culture-arts', 'Culture &<br>Arts', 'images/island-calendar/culture.png'),
    ('wellness-lifestyle', 'Wellness &<br>Lifestyle', 'images/island-calendar/Wellness.png'),
    ('secret-pop-ups', 'Secret &<br>Pop-Ups', 'images/island-calendar/Secret.png'),
]

# The two round pills beside the calendar
PILL_SLUGS = ['festival', 'live-music']


def _weekend_range(today):
    """Saturday and Sunday of the coming weekend (or the one we are in)."""
    if today.weekday() == 6:                       # Sunday
        saturday = today - timedelta(days=1)
    else:
        saturday = today + timedelta(days=(5 - today.weekday()))
    return saturday, saturday + timedelta(days=1)


def _parse_date(value):
    try:
        return date.fromisoformat(value)
    except (TypeError, ValueError):
        return None


def _build_calendar(year, month, selected, event_dates, today):
    """The small month grid in the sidebar. Weeks start on Sunday."""
    cal = calendar.Calendar(firstweekday=6)
    return [
        [
            {
                'number': d.day,
                'iso': d.isoformat(),
                'in_month': d.month == month,
                'selected': d == selected,
                'is_today': d == today,
                'has_event': d in event_dates,
            }
            for d in week
        ]
        for week in cal.monthdatescalendar(year, month)
    ]


def island_calendar(request):
    """
    Island Calendar.

    Everything on the page comes from the Event table. The filters are all
    in the address bar, so a filtered view can be bookmarked or shared:

        ?q=neon              search box
        ?region=west         "All Mauritius" dropdown  (Destination -> Region)
        ?when=weekend        "Any date" dropdown
        ?category=festival   filter pills and the "What to expect" tiles
        ?day=2026-10-17      a day clicked in the small calendar
        ?month=2026-11       the month arrows
    """
    today = timezone.localdate()

    # ---------- read the filters ----------
    region_slugs = list(Region.objects.values_list('slug', flat=True))
    category_slugs = list(Category.objects.values_list('slug', flat=True))

    requested_region = request.GET.get('region', 'all')
    requested_when = request.GET.get('when', 'any')
    requested_category = request.GET.get('category', '')

    filters = {
        'q': request.GET.get('q', '').strip(),
        'region': requested_region if requested_region in region_slugs else 'all',
        'when': requested_when if requested_when in dict(WHEN_CHOICES) else 'any',
        'category': requested_category if requested_category in category_slugs else '',
        'day': _parse_date(request.GET.get('day')),
    }
    is_filtering = bool(
        filters['q'] or filters['category'] or filters['day']
        or filters['region'] != 'all' or filters['when'] != 'any'
    )

    # ---------- everything still to come ----------
    upcoming_qs = (Event.objects
                   .filter(date__gte=today, show_on_calendar=True)
                   .select_related('category', 'destination', 'destination__region'))

    events = upcoming_qs

    if filters['q']:
        events = events.filter(
            Q(title__icontains=filters['q'])
            | Q(location_name__icontains=filters['q'])
            | Q(short_description__icontains=filters['q'])
            | Q(category__name__icontains=filters['q'])
        )

    if filters['region'] != 'all':
        events = events.filter(destination__region__slug=filters['region'])

    if filters['category']:
        events = events.filter(category__slug=filters['category'])



    if filters['when'] == 'today':
        events = events.filter(date=today)
    elif filters['when'] == 'weekend':
        saturday, sunday = _weekend_range(today)
        events = events.filter(date__range=(saturday, sunday))
    elif filters['when'] == 'month':
        events = events.filter(date__year=today.year, date__month=today.month)

    ordered_events = list(events.order_by('date'))
    upcoming_events = [e for e in ordered_events if e.calendar_section == 'upcoming'][:3]
    weekend_events = [e for e in ordered_events if e.calendar_section == 'weekend'][:3]

    used_ids = {e.id for e in upcoming_events + weekend_events}
    leftovers = [e for e in ordered_events if e.id not in used_ids]
    while len(upcoming_events) < 3 and leftovers:
        upcoming_events.append(leftovers.pop(0))
    while len(weekend_events) < 3 and leftovers:
        weekend_events.append(leftovers.pop(0))

    only_weekend = False

    # ---------- the small calendar in the sidebar ----------
    month_date = _parse_date((request.GET.get('month') or '') + '-01')
    if month_date is None:
        month_date = (filters['day'] or today).replace(day=1)
    prev_month = (month_date - timedelta(days=1)).replace(day=1)
    next_month = (month_date + timedelta(days=32)).replace(day=1)

    # ---------- the pills and the "What to expect" tiles ----------
    categories = {c.slug: c for c in Category.objects.all()}
    pills = [categories[slug] for slug in PILL_SLUGS if slug in categories]
    tiles = [
        {'slug': slug, 'label': label, 'image': image}
        for slug, label, image in EXPECT_TILES
    ]

    context = {
        # events
        'upcoming_events': upcoming_events,
        'weekend_events': weekend_events,
        'only_weekend': only_weekend,

        # filters
        'filters': filters,
        'is_filtering': is_filtering,
        'regions': Region.objects.all(),
        'when_choices': WHEN_CHOICES,
        'pills': pills,
        'tiles': tiles,
        'active_category': categories.get(filters['category']),
        'active_region': Region.objects.filter(slug=filters['region']).first(),
        'when_label': dict(WHEN_CHOICES)[filters['when']],

        # sidebar calendar
        'month_label': f"{calendar.month_name[month_date.month].upper()} {month_date.year}",
        'prev_month': prev_month.strftime('%Y-%m'),
        'next_month': next_month.strftime('%Y-%m'),
        'weekday_names': ['Su', 'Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa'],
        'weeks': _build_calendar(
            month_date.year, month_date.month,
            selected=filters['day'] or today,
            event_dates=set(upcoming_qs.values_list('date', flat=True)),
            today=today,
        ),

        # map pins: the next three events that have a destination
        'map_events': list(upcoming_qs.exclude(destination=None)[:3]),

        'today': today,
    }
    return render(request, 'experiences/island_calendar.html', context)


def _booking_display_title(booking):
    """A booking is for EITHER an Event OR a Package (apps.bookings.Booking) -
    never assume booking.event exists."""
    if booking.event_id:
        return booking.event.title
    if booking.package_id:
        return booking.package.title
    return f'booking {booking.reference}'


@login_required
def my_experiences(request):
    """My Experiences page: fetches real database instances for the authenticated user."""
    today = timezone.localdate()
    user = request.user

    bookings = (Booking.objects.filter(user=user)
                .select_related('event', 'package', 'payment')
                .order_by('-created_at'))

    # Give every booking a safe display title up front, so the template never
    # has to touch booking.event directly (it can be null for package bookings).
    for booking in bookings:
        booking.display_title = _booking_display_title(booking)

    # Build the Previous/Upcoming Experiences cards from the bookings
    # themselves (not just the Event table) so package bookings show up too.
    # Each card is a plain dict so the existing template (exp.title, exp.date,
    # exp.image, ...) keeps working unchanged.
    cards = {}
    for booking in bookings:
        if booking.status == 'cancelled':
            continue
        if booking.event_id:
            key = ('event', booking.event_id)
            if key in cards:
                continue
            event = booking.event
            cards[key] = {
                'title': event.title,
                'date': event.date,
                'image': event.image,
                'location_name': event.location_name or (event.destination.name if event.destination_id else ''),
                'rating': event.rating,
                'slug': event.slug,
            }
        elif booking.package_id:
            key = ('package', booking.package_id)
            if key in cards:
                continue
            package = booking.package
            cards[key] = {
                'title': package.title,
                'date': booking.preferred_date or booking.created_at.date(),
                'image': package.image,
                'location_name': package.location,
                'rating': package.rating,
                'slug': None,
            }

    previous_experiences = sorted(
        (card for card in cards.values() if card['date'] < today),
        key=lambda card: card['date'], reverse=True,
    )
    upcoming_experiences = sorted(
        (card for card in cards.values() if card['date'] >= today),
        key=lambda card: card['date'],
    )

    reviews = Review.objects.filter(user=user).select_related('event').order_by('-created_at')
    favourites = Favourite.objects.filter(user=user).select_related('event').order_by('-created_at')

    reviewed_event_ids = reviews.values_list('event_id', flat=True)
    reviewable = Event.objects.filter(bookings__user=user, date__lt=today).exclude(id__in=reviewed_event_ids)

    return render(request, 'experiences/my_experiences.html', {
        'previous_experiences': previous_experiences,
        'upcoming_experiences': upcoming_experiences,
        'bookings': bookings,
        'reviews': reviews,
        'favourites': favourites,
        'reviewable': reviewable,
        'star_range': range(1, 6),
    })


@login_required
def cancel_booking(request, pk):
    booking = get_object_or_404(Booking.objects.select_related('event', 'package'), pk=pk)
    if booking.user != request.user and not request.user.is_staff:
        raise PermissionDenied
    if request.method == 'POST':
        booking.status = 'cancelled'
        booking.save()
        messages.success(request, f'Your booking for {_booking_display_title(booking)} has been cancelled.')
    return redirect('experiences:my_experiences')


@login_required
def add_review(request):
    if request.method == 'POST':
        event_id = request.POST.get('event')
        rating = request.POST.get('rating')
        comment = request.POST.get('comment', '').strip()

        event = get_object_or_404(Event, pk=event_id)

        if Review.objects.filter(user=request.user, event=event).exists():
            messages.error(request, "You've already reviewed this experience.")
        elif not rating or not comment:
            messages.error(request, 'Please choose a rating and write a comment.')
        else:
            Review.objects.create(user=request.user, event=event, rating=int(rating), comment=comment)
            messages.success(request, 'Thanks for your review!')

    return redirect('experiences:my_experiences')


@login_required
def edit_review(request, pk):
    review = get_object_or_404(Review, pk=pk)
    if review.user != request.user and not request.user.is_staff:
        raise PermissionDenied

    if request.method == 'POST':
        rating = request.POST.get('rating')
        comment = request.POST.get('comment', '').strip()

        if not rating or not comment:
            messages.error(request, 'Please choose a rating and write a comment.')
        else:
            review.rating = int(rating)
            review.comment = comment
            review.save()
            messages.success(request, 'Your review has been updated.')

    return redirect('experiences:my_experiences')


@login_required
def delete_review(request, pk):
    review = get_object_or_404(Review, pk=pk)
    if review.user != request.user and not request.user.is_staff:
        raise PermissionDenied

    if request.method == 'POST':
        review.delete()
        messages.success(request, 'Your review has been deleted.')

    return redirect('experiences:my_experiences')


@login_required
def toggle_favourite(request, pk=None, slug=None):
    """Toggle a Favourite for the logged-in user. Reachable by pk (My Experiences
    page) or by slug (Explore Board). A fetch/AJAX POST gets a small JSON reply;
    a normal form POST redirects back to My Experiences as before."""
    if slug:
        event = get_object_or_404(Event, slug=slug)
    else:
        event = get_object_or_404(Event, pk=pk)

    is_favourite = None
    if request.method == 'POST':
        favourite = Favourite.objects.filter(user=request.user, event=event).first()
        if favourite:
            favourite.delete()
            is_favourite = False
            messages.success(request, f'Removed {event.title} from your favourites.')
        else:
            Favourite.objects.create(user=request.user, event=event)
            is_favourite = True
            messages.success(request, f'Added {event.title} to your favourites.')

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'ok': True, 'is_favourite': is_favourite, 'slug': event.slug})

    return redirect('experiences:my_experiences')







def _bot_reply(message):
    lowered = message.lower()
    for entry in FAQEntry.objects.all():
        if entry.keyword.lower() in lowered:
            return entry.answer
    return ("I'm not totally sure about that one! You can type 'agent' or click "
            "'Talk to an Agent' below and one of our team will help you directly.")

def chat_start(request):
    """Called once when the chat window is first opened; creates or resumes a session."""
    session_key = request.session.get('chat_session_key')
    session = ChatSession.objects.filter(session_key=session_key).first() if session_key else None

    if not session:
        session_key = str(uuid.uuid4())
        session = ChatSession.objects.create(
            session_key=session_key,
            user=request.user if request.user.is_authenticated else None,
        )
        request.session['chat_session_key'] = session_key
        ChatMessage.objects.create(
            session=session, sender='bot',
            text="Hi! 👋 Ask me anything about events, bookings, or activities — or request a live agent anytime."
        )

    messages = list(session.messages.values('id', 'sender', 'text', 'created_at'))
    return JsonResponse({
        'session_id': session.id,
        'is_live_requested': session.is_live_requested,
        'messages': [
            {'id': m['id'], 'sender': m['sender'], 'text': m['text'], 'time': m['created_at'].strftime('%H:%M')}
            for m in messages
        ],
    })


@require_POST
def chat_send(request):
    data = json.loads(request.body)
    session_id = data.get('session_id')
    text = (data.get('message') or '').strip()

    session = get_object_or_404(ChatSession, id=session_id)
    if not text:
        return JsonResponse({'ok': False})

    ChatMessage.objects.create(session=session, sender='user', text=text)

    if not session.is_live_requested:
        if 'agent' in text.lower():
            session.is_live_requested = True
            session.save()
            ChatMessage.objects.create(
                session=session, sender='bot',
                text="Connecting you to a live agent — someone from our team will reply here shortly."
            )
        else:
            ChatMessage.objects.create(session=session, sender='bot', text=_bot_reply(text))

    return JsonResponse({'ok': True})


@require_POST
def chat_request_agent(request):
    data = json.loads(request.body)
    session = get_object_or_404(ChatSession, id=data.get('session_id'))
    if not session.is_live_requested:
        session.is_live_requested = True
        session.save()
        ChatMessage.objects.create(
            session=session, sender='bot',
            text="Connecting you to a live agent — someone from our team will reply here shortly."
        )
    return JsonResponse({'ok': True})


def chat_poll(request, session_id):
    """Frontend calls this every few seconds to check for new messages."""
    session = get_object_or_404(ChatSession, id=session_id)
    since_id = request.GET.get('since', 0)
    messages = session.messages.filter(id__gt=since_id).values('id', 'sender', 'text', 'created_at')
    return JsonResponse({
        'messages': [
            {'id': m['id'], 'sender': m['sender'], 'text': m['text'], 'time': m['created_at'].strftime('%H:%M')}
            for m in messages
        ],
    })




def experience_category(request, category_slug):
    """Any category landing page (Nature, Food, Culture, History, Experiences).
    One view for all of them — which page renders is decided entirely by the
    category_slug in the URL, and the content comes from admin."""
    category = get_object_or_404(Category, slug=category_slug)
    items = Experience.objects.filter(category=category, is_active=True)
    kinds = sorted({item.kind for item in items if item.kind})
    return render(request, 'experiences/experience_category.html', {
        'category': category,
        'items': items,
        'kinds': kinds,
    })


# ======================================================================
# from the old "bookings" app
# ======================================================================

@login_required
def reserve(request, slug):
    """Book Now -> Reserve Your Experience (for Events)."""
    event = get_object_or_404(Event, slug=slug)
    profile, _ = Profile.objects.get_or_create(user=request.user)

    if event.is_past or event.spots_left == 0:
        messages.error(request, 'This event is no longer available.')
        return redirect(event.get_absolute_url())

    initial = {'full_name': request.user.get_full_name(), 'email': request.user.email, 'phone': profile.phone}
    form = ReserveForm(request.POST or None, event=event, initial=initial)
    if request.method == 'POST' and form.is_valid():
        booking = form.save(commit=False)
        booking.user = request.user
        booking.event = event
        booking.save()
        return redirect('bookings:checkout', reference=booking.reference)
    return render(request, 'bookings/reserve.html', {'event': event, 'form': form})


@login_required
def reserve_experience(request):
    """Reserve Package button (Guides & Packages / Guide Profile) -> this page.

    The package is read from ?package=<slug> in the URL, exactly like the
    buttons on guides_packages.html and guide_detail.html already send it.
    """
    package_slug = request.GET.get('package') or request.POST.get('package')
    package = get_object_or_404(Package, slug=package_slug) if package_slug else None
    if package is None:
        messages.error(request, 'No package was specified.')
        return redirect('destinations:guides_packages')

    profile, _ = Profile.objects.get_or_create(user=request.user)
    initial = {'full_name': request.user.get_full_name(), 'email': request.user.email, 'phone': profile.phone}
    form = ReservePackageForm(request.POST or None, package=package, initial=initial)

    if request.method == 'POST' and form.is_valid():
        booking = form.save(commit=False)
        booking.user = request.user
        booking.package = package
        booking.save()
        messages.success(request, 'Your booking request has been sent!')
        return redirect('bookings:checkout', reference=booking.reference)

    return render(request, 'bookings/reserve_experience.html', {'package': package, 'form': form})


@login_required
def checkout(request, reference):
    """Reserve Your Experience -> Secure Checkout."""
    booking = get_object_or_404(Booking.objects.select_related('event', 'package'), reference=reference, user=request.user)
    if booking.status == Booking.Status.CONFIRMED:
        return redirect('bookings:confirmation', reference=booking.reference)

    form = CheckoutForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        booking.full_name = form.cleaned_data['full_name']
        booking.email = form.cleaned_data['email']
        booking.phone = form.cleaned_data['phone']

        method = form.cleaned_data['method']

        Payment.objects.update_or_create(booking=booking, defaults={
            'method': method,
            'amount': booking.total_price,
            'status': Payment.Status.PAID,
            'card_last4': form.cleaned_data['card_number'][-4:] if method == Payment.Method.CARD else '',
            'paid_at': timezone.now(),
        })
        booking.status = Booking.Status.CONFIRMED
        booking.save()
        messages.success(request, 'Booking confirmed!')
        return redirect('bookings:confirmation', reference=booking.reference)

    short_labels = {'juice': 'JUICE', 'card': 'Card', 'myt': 'My.T', 'qr': 'QR'}
    selected_method = request.POST.get('method') or 'juice'

    payment_methods = [
        {'value': value, 'label': label, 'short': short_labels[value], 'muted': False}
        for value, label in Payment.Method.choices
    ]

    return render(request, 'bookings/checkout.html', {
        'booking': booking,
        'form': form,
        'payment_methods': payment_methods,
        'selected_method': selected_method,
        'selected_short': short_labels.get(selected_method, ''),
        'ticket_line': f'General Admission x{booking.number_of_people}',
        'subtotal_display': f'{(booking.package.price if booking.package_id else booking.event.price) * booking.number_of_people:,.0f}',
        'fee_display': f'{booking.booking_fee:,.0f}',
        'total_display': f'{booking.total_price:,.0f}',
    })


@login_required
def confirmation(request, reference):
    booking = get_object_or_404(Booking.objects.select_related('event', 'package'), reference=reference, user=request.user)
    return render(request, 'bookings/confirmation.html', {'booking': booking})


# ======================================================================
# from the old "admin_dashboard" app
# ======================================================================

@staff_member_required
def dashboard(request):
    today = timezone.localdate()
    revenue = Payment.objects.filter(status=Payment.Status.PAID).aggregate(total=Sum('amount'))['total'] or 0
    return render(request, 'admin_dashboard/dashboard.html', {
        'stats': {
            'upcoming_events': Event.objects.filter(date__gte=today).count(),
            'destinations': Destination.objects.count(),
            'bookings': Booking.objects.count(),
            'customers': Profile.objects.filter(user__is_staff=False).count(),
            'revenue': revenue,
        },
        'recent_bookings': Booking.objects.select_related('user', 'event')[:10],
        'upcoming_events': Event.objects.filter(date__gte=today)[:5],
    })