import calendar
from datetime import date, timedelta

from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, render
from django.utils import timezone

from apps.bookings.models import Booking
from apps.destinations.models import Region

from .models import Category, Event

CALENDAR_ONLY_CATEGORIES = [
    'festival', 'live-music', 'food-street-eats', 'nightlife-parties',
    'nature-outdoor', 'culture-arts', 'wellness-lifestyle', 'secret-pop-ups',
]

def all_events(request):
    """All Events & Activities page. Filter: ?category=hiking"""
    events = (Event.objects
              .filter(date__gte=timezone.localdate())
              .exclude(category__slug__in=CALENDAR_ONLY_CATEGORIES)
              .select_related('category', 'destination'))
    selected = request.GET.get('category')
    if selected:
        events = events.filter(category__slug=selected)
    return render(request, 'experiences/all_events.html', {
        'events': events,
        'categories': Category.objects.exclude(slug__in=CALENDAR_ONLY_CATEGORIES),
        'selected_category': selected,
    })




def event_detail(request, slug):
    event = get_object_or_404(Event.objects.select_related('category', 'destination'), slug=slug)
    return render(request, 'experiences/event_detail.html', {'event': event})


# ======================================================================
# ISLAND CALENDAR
# ======================================================================

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
                   .filter(date__gte=today)
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

   # ---------- split into THIS WEEKEND and UPCOMING ----------
      # ---------- always show 3 + 3 events, regardless of date ----------
    ordered_events = list(events.order_by('date'))
    upcoming_events = ordered_events[:3]
    weekend_events = ordered_events[3:6]
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


@login_required
def my_experiences(request):
    """My Experiences page: the logged-in user's bookings (data from the bookings app)."""
    bookings = Booking.objects.filter(user=request.user).select_related('event')
    today = timezone.localdate()
    return render(request, 'experiences/my_experiences.html', {
        'upcoming': [b for b in bookings if b.event.date >= today and b.status != 'cancelled'],
        'past': [b for b in bookings if b.event.date < today or b.status == 'cancelled'],
    })