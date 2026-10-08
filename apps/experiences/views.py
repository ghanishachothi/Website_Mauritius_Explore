import calendar
from datetime import date, time as time_min, timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone


import json
import uuid

from django.http import JsonResponse
from django.views.decorators.http import require_POST

from apps.bookings.models import Booking
from apps.destinations.models import Region

from .models import Category, ChatMessage, ChatSession, Event, Experience, FAQEntry, Review, Favourite

from django.http import Http404

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

    cheapest = Event.objects.filter(date__gte=today).order_by('price').first()
    price_min = 0
    price_max = 10000
    if cheapest and float(cheapest.price) > 0:
        price_min = int(float(cheapest.price))
    dearest = Event.objects.filter(date__gte=today).order_by('-price').first()
    if dearest and float(dearest.price) > 0:
        price_max = min(10000, int(float(dearest.price)) + 500)

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
        'price_min': price_min,
        'price_max': price_max,
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
def toggle_favourite(request, pk):
    event = get_object_or_404(Event, pk=pk)
    if request.method == 'POST':
        favourite = Favourite.objects.filter(user=request.user, event=event).first()
        if favourite:
            favourite.delete()
            messages.success(request, f'Removed {event.title} from your favourites.')
        else:
            Favourite.objects.create(user=request.user, event=event)
            messages.success(request, f'Added {event.title} to your favourites.')

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