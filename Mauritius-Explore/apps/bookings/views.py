from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from apps.experiences.models import Event
from apps.users.models import Profile

from .forms import CheckoutForm, ReserveForm
from .models import Booking, Payment


@login_required
def reserve(request, slug):
    """Book Now -> Reserve Your Experience."""
    event = get_object_or_404(Event, slug=slug)
    profile, _ = Profile.objects.get_or_create(user=request.user)

    if not profile.can_book:
        messages.error(request, 'Viewer accounts cannot make bookings.')
        return redirect(event.get_absolute_url())
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
def checkout(request, reference):
    """Reserve Your Experience -> Secure Checkout."""
    booking = get_object_or_404(Booking.objects.select_related('event'), reference=reference, user=request.user)
    if booking.status == Booking.Status.CONFIRMED:
        return redirect('bookings:confirmation', reference=booking.reference)

    form = CheckoutForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        method = form.cleaned_data['method']
        paid_now = method != Payment.Method.CASH
        Payment.objects.update_or_create(booking=booking, defaults={
            'method': method,
            'amount': booking.total_price,
            'status': Payment.Status.PAID if paid_now else Payment.Status.PENDING,
            'card_last4': form.cleaned_data['card_number'][-4:] if method == Payment.Method.CARD else '',
            'paid_at': timezone.now() if paid_now else None,
        })
        booking.status = Booking.Status.CONFIRMED
        booking.save()
        messages.success(request, 'Booking confirmed!')
        return redirect('bookings:confirmation', reference=booking.reference)
    return render(request, 'bookings/checkout.html', {'booking': booking, 'form': form})


@login_required
def confirmation(request, reference):
    booking = get_object_or_404(Booking.objects.select_related('event'), reference=reference, user=request.user)
    return render(request, 'bookings/confirmation.html', {'booking': booking})
