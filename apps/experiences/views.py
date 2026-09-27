import calendar
from collections import defaultdict
from datetime import date

from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render
from django.utils import timezone

from django.db.models import Q


from apps.bookings.models import Booking

from .models import Category, Event


def all_events(request):
    """All Events & Activities page. Filter: ?category=hiking  Search: ?q=kayak"""
    query = request.GET.get('q', '').strip()
    selected = request.GET.get('category')

    events = (Event.objects
              .filter(date__gte=timezone.localdate())
              .exclude(category__is_calendar_only=True)
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
        'categories': Category.objects.exclude(is_calendar_only=True),
        'selected_category': selected,
        'query': query,
    })

def event_detail(request, slug):
    event = get_object_or_404(Event.objects.select_related('category', 'destination'), slug=slug)
    return render(request, 'experiences/event_detail.html', {'event': event})


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
    for event in events:
        by_day[event.date].append(event)

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
