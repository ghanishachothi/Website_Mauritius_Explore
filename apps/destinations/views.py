import math
from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation
from types import SimpleNamespace

from django.db.models import Q
from django.shortcuts import get_object_or_404, render
from django.utils import timezone

from apps.experiences.models import Category, Event

from .models import Destination, Guide, Package, Region


def _event_duration_hours(event):
    if not event.start_time or not event.end_time:
        return None
    start = datetime.combine(event.date, event.start_time)
    end = datetime.combine(event.date, event.end_time)
    if end <= start:
        end += timedelta(days=1)
    return math.ceil((end - start).total_seconds() / 3600)


def explore_island(request):
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

    return render(request, 'destinations/explore_island.html', {
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
    """Show a region's places, upcoming activities, packages, and guides."""
    region = get_object_or_404(Region, slug=slug)
    destinations = region.destinations.all()
    if region.slug == 'east':
        east_place_order = {
            'ile-aux-cerfs': 0,
            'belle-mare': 1,
            'grse-waterfall': 2,
            'poste-de-flacq-temple': 3,
            'bras-deau': 4,
            'trou-deau-douce-lagoon': 5,
        }
        destinations = sorted(
            destinations,
            key=lambda destination: (
                east_place_order.get(destination.slug, len(east_place_order)),
                destination.name,
            ),
        )
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
        'destinations': destinations,
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
    """Guide profile page (e.g. Aliyah C., John W.)."""
    guide = get_object_or_404(Guide, slug=slug, is_active=True)
    return render(request, 'destinations/guide_detail.html', {
        'guide': guide,
        'packages': guide.packages.all(),
    })


def explore_board(request):
    """Explore Board page, filterable by region: /destinations/board/?region=north"""
    destinations = Destination.objects.select_related('region')
    selected = request.GET.get('region')
    if selected:
        destinations = destinations.filter(region__slug=selected)
    return render(request, 'destinations/explore_board.html', {
        'destinations': destinations,
        'regions': Region.objects.all(),
        'selected_region': selected,
    })



from django.http import Http404
def reserve_experience(request):
    """Placeholder - real page not merged into main yet."""
    raise Http404("This page is not available yet.")