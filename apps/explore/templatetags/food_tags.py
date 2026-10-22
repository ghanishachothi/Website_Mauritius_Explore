from django import template
from django.utils import timezone

register = template.Library()


@register.simple_tag
def food_context(slug):
    """For a card slug: is it a Food experience, which places serve it, and bookable food events."""
    from apps.explore.models import Event, Experience, FoodSpot
    exp = Experience.objects.filter(slug=slug, category__name__icontains='food').first()
    if exp is None:
        return {'is_food': False, 'spots': [], 'events': []}
    spots = list(FoodSpot.objects.filter(experiences=exp, is_active=True))
    events = list(Event.objects.filter(category__name__icontains='food', date__gte=timezone.localdate())
                  .order_by('date')[:4])
    return {'is_food': True, 'spots': spots, 'events': events, 'exp': exp}


@register.simple_tag(takes_context=True)
def my_booking(context):
    """The visitor's own booking named by ?booking=<reference>, or None."""
    request = context.get('request')
    if request is None or not request.user.is_authenticated:
        return None
    ref = request.GET.get('booking')
    if not ref:
        return None
    from apps.explore.models import Booking
    b = Booking.objects.filter(reference=ref, user=request.user).select_related('event', 'package').first()
    if b is None or b.status == 'cancelled':
        return None
    return b
