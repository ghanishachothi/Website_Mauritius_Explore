import calendar
from collections import defaultdict
from datetime import date

from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render
from django.utils import timezone

from apps.bookings.models import Booking

from .models import Category, Event, Experience

from django.http import Http404

def all_events(request):
    """All Events & Activities page. Filter: ?category=hiking"""
    events = Event.objects.filter(date__gte=timezone.localdate()).select_related('category', 'destination')
    selected = request.GET.get('category')
    if selected:
        events = events.filter(category__slug=selected)
    return render(request, 'experiences/all_events.html', {
        'events': events,
        'categories': Category.objects.all(),
        'selected_category': selected,
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


def taste_mauritius(request):
    """Taste Mauritius (food frame): food experience cards from the database."""
    category = get_object_or_404(Category, slug='food')
    items = Experience.objects.filter(category=category, is_active=True)
    return render(request, 'experiences/food.html', {
        'items': items,
        'category': category,
        'kinds': items.exclude(kind='').values_list('kind', flat=True).distinct(),
    })


def experience_insight(request):
    """Placeholder - page not built yet."""
    raise Http404("This page is not available yet.")


def explore_your_way(request):
    """Placeholder - page not built yet."""
    raise Http404("This page is not available yet.")


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