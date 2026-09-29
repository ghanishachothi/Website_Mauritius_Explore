import calendar
from collections import defaultdict
from datetime import date

from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.utils import timezone

from apps.bookings.models import Booking
from apps.destinations.models import Region

from .models import Category, Event


def all_events(request, *, page_title='All Events & Activities'):
    """All Events & Activities page. Filter: ?category=hiking"""
    events = Event.objects.filter(date__gte=timezone.localdate()).select_related('category', 'destination')
    selected = request.GET.get('category')
    if selected:
        events = events.filter(category__slug=selected)
    return render(request, 'experiences/all_events.html', {
        'events': events,
        'categories': Category.objects.all(),
        'selected_category': selected,
        'page_title': page_title,
    })


def experience_insight(request):
    return all_events(request, page_title='Experience Insight')


def explore_your_way(request):
    today = timezone.localdate()
    events = Event.objects.filter(date__gte=today).select_related(
        'category', 'destination', 'destination__region'
    )
    query = request.GET.get('q', '').strip()
    selected_category = request.GET.get('category', '').strip()
    selected_region = request.GET.get('region', '').strip()

    if query:
        events = events.filter(
            Q(title__icontains=query)
            | Q(short_description__icontains=query)
            | Q(description__icontains=query)
            | Q(category__name__icontains=query)
            | Q(destination__name__icontains=query)
        )
    if selected_category:
        events = events.filter(category__slug=selected_category)
    if selected_region:
        events = events.filter(destination__region__slug=selected_region)

    return render(request, 'experiences/explore_your_way.html', {
        'events': events,
        'categories': Category.objects.all(),
        'regions': Region.objects.all(),
        'query': query,
        'selected_category': selected_category,
        'selected_region': selected_region,
    })


def event_detail(request, slug):
    event = get_object_or_404(
        Event.objects.select_related('category', 'destination', 'guide', 'destination__region'),
        slug=slug,
    )

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
        ('Experiences', reverse('experiences:experience_insight')),
        ('All Experiences', reverse('experiences:all_events')),
        (event.title, None),
    ]

    return render(request, 'experiences/event_detail.html', {
        'event': event,
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
        'review_count_label': f'{event.review_count}',
    })


def island_calendar(request):
    """Island Calendar page. Month switch: ?year=2026&month=10"""
    today = timezone.localdate()
    try:
        year = int(request.GET.get('year', today.year))
        month = int(request.GET.get('month', today.month))
        date(year, month, 1)
    except ValueError:
        year, month = today.year, today.month

    weeks = calendar.Calendar(firstweekday=0).monthdatescalendar(year, month)
    events = Event.objects.filter(date__gte=weeks[0][0], date__lte=weeks[-1][-1])
    by_day = defaultdict(list)
    for ev in events:
        by_day[ev.date].append(ev)

    calendar_weeks = [
        [{'date': d, 'in_month': d.month == month, 'is_today': d == today, 'events': by_day.get(d, [])}
         for d in week]
        for week in weeks
    ]
    prev_year, prev_month = (year - 1, 12) if month == 1 else (year, month - 1)
    next_year, next_month = (year + 1, 1) if month == 12 else (year, month + 1)

    return render(request, 'experiences/island_calendar.html', {
        'calendar_weeks': calendar_weeks,
        'month_name': calendar.month_name[month],
        'year': year,
        'prev_year': prev_year, 'prev_month': prev_month,
        'next_year': next_year, 'next_month': next_month,
        'month_events': [e for e in events if e.date.month == month],
    })


@login_required
def my_experiences(request):
    """My Experiences page: the logged-in user's bookings (data from the bookings app)."""
    bookings = Booking.objects.filter(user=request.user).select_related('event')
    today = timezone.localdate()
    return render(request, 'experiences/my_experiences.html', {
        'upcoming': [b for b in bookings if b.event.date >= today and b.status != 'cancelled'],
        'past': [b for b in bookings if b.event.date < today or b.status == 'cancelled'],
    })

