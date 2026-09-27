from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from apps.experiences.models import Event
from apps.users.models import Profile

from .forms import CheckoutForm, ReserveForm
from .models import Booking, Payment


@login_required
def checkout(request, reference):
    """Reserve Your Experience -> Secure Checkout."""
    booking = get_object_or_404(Booking.objects.select_related('event'), reference=reference, user=request.user)
    if booking.status == Booking.Status.CONFIRMED:
        return redirect('bookings:confirmation', reference=booking.reference)

    form = CheckoutForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        method = form.cleaned_data['method']
        Payment.objects.update_or_create(booking=booking, defaults={
            'method': method,
            'amount': booking.total_price,
            'status': Payment.Status.PAID,
            'card_last4': form.cleaned_data['card_number'][-4:] if method == Payment.Method.CARD else '',
            'paid_at': timezone.now(),
        })
        booking.status = Booking.Status.CONFIRMED
        booking.save()
        messages.success(request, 'Booking confirmed!')
        return redirect('bookings:confirmation', reference=booking.reference)

    short_labels = {'juice': 'JUICE', 'card': 'Card', 'myt': 'My.T', 'qr': 'QR'}
    selected_method = request.POST.get('method') or 'juice'

    payment_methods = [
        {'value': value, 'label': label, 'short': short_labels[value], 'muted': False}
        for value, label in Payment.Method.choices
    ]

    return render(request, 'bookings/checkout.html', {
        'booking': booking,
        'form': form,
        'payment_methods': payment_methods,
        'selected_method': selected_method,
        'selected_short': short_labels.get(selected_method, ''),
        'ticket_line': f'General Admission x{booking.number_of_people}',
        'subtotal_display': f'{booking.event.price * booking.number_of_people:,.0f}',
        'fee_display': f'{booking.booking_fee:,.0f}',
        'total_display': f'{booking.total_price:,.0f}',
    })