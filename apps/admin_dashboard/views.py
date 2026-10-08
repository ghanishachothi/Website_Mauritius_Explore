from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Sum
from django.shortcuts import render
from django.utils import timezone

from apps.bookings.models import Booking, Payment
from apps.destinations.models import Destination
from apps.experiences.models import Event
from apps.users.models import Profile


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