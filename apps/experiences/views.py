import calendar
from collections import defaultdict
from datetime import date

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from apps.bookings.models import Booking

from .models import Category, Event, FoodExperience, Favourite, Review


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
    """My Experiences page: bookings, reviews and favourites for the logged-in user."""
    today = timezone.localdate()
    user = request.user

    bookings = (Booking.objects.filter(user=user)
                .select_related('event', 'payment')
                .order_by('-created_at'))

    previous_experiences = (
        Event.objects.filter(bookings__user=user, date__lt=today)
        .distinct().order_by('-date')
    )
    upcoming_experiences = (
        Event.objects.filter(bookings__user=user, date__gte=today)
        .exclude(bookings__user=user, bookings__status='cancelled')
        .distinct().order_by('date')
    )

    reviews = Review.objects.filter(user=user).select_related('event').order_by('-created_at')
    favourites = Favourite.objects.filter(user=user).select_related('event').order_by('-created_at')

    reviewed_event_ids = reviews.values_list('event_id', flat=True)
    reviewable = previous_experiences.exclude(id__in=reviewed_event_ids)

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
    booking = get_object_or_404(Booking, pk=pk)
    if booking.user != request.user and not request.user.is_staff:
        raise PermissionDenied
    if request.method == 'POST':
        booking.status = 'cancelled'
        booking.save()
        messages.success(request, f'Your booking for {booking.event.title} has been cancelled.')
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
            Review.objects.create(user=request.user, event=event, rating=rating, comment=comment)
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
        if rating and comment:
            review.rating = rating
            review.comment = comment
            review.save()
            messages.success(request, 'Your review has been updated.')
        else:
            messages.error(request, 'Please choose a rating and write a comment.')
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


def taste_mauritius(request):
    """Taste Mauritius (food frame): food experience cards from the database."""
    return render(request, 'experiences/food.html', {
        'items': FoodExperience.objects.filter(is_active=True),
        'kinds': FoodExperience.Kind.choices,
    })


def experience_insight(request):
    """Placeholder - page not built yet."""
    raise Http404("This page is not available yet.")


def explore_your_way(request):
    """Placeholder - page not built yet."""
    raise Http404("This page is not available yet.")
