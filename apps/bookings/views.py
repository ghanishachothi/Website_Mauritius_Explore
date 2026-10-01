from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
 
from apps.destinations.models import Package
from apps.experiences.models import Event
from apps.users.models import Profile
 
from .forms import CheckoutForm, ReserveForm, ReservePackageForm
from .models import Booking, Payment
 
 
@login_required

def reserve(request, slug):
    """Book Now -> Reserve Your Experience (for Events)."""
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
 
 
def reserve_experience(request):
    """Reserve Package button (Guides & Packages / Guide Profile) -> this page.
 
    The package is read from ?package=<slug> in the URL, exactly like the
    buttons on guides_packages.html and guide_detail.html already send it.
    """
    package_slug = request.GET.get('package') or request.POST.get('package')
    package = get_object_or_404(Package, slug=package_slug) if package_slug else None
    if package is None:
        messages.error(request, 'No package was specified.')
        return redirect('destinations:guides_packages')
 
    if not request.user.is_authenticated:
        return render(request, 'bookings/reserve_experience.html', {
            'package': package,
            'form': ReservePackageForm(package=package),
        })
 
    profile, _ = Profile.objects.get_or_create(user=request.user)
    initial = {'full_name': request.user.get_full_name(), 'email': request.user.email, 'phone': profile.phone}
    form = ReservePackageForm(request.POST or None, package=package, initial=initial)
 
    if request.method == 'POST' and form.is_valid():
        booking = form.save(commit=False)
        booking.user = request.user
        booking.package = package
        booking.save()
        messages.success(request, 'Your booking request has been sent!')
        return redirect('bookings:checkout', reference=booking.reference)
 
    return render(request, 'bookings/reserve_experience.html', {'package': package, 'form': form})
 
 
@login_required
def checkout(request, reference):
    """Reserve Your Experience -> Secure Checkout."""
    booking = get_object_or_404(Booking.objects.select_related('event', 'package'), reference=reference, user=request.user)
    if booking.status == Booking.Status.CONFIRMED:
        return redirect('bookings:confirmation', reference=booking.reference)
 
    form = CheckoutForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        booking.full_name = form.cleaned_data['full_name']
        booking.email = form.cleaned_data['email']
        booking.phone = form.cleaned_data['phone']

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
        'subtotal_display': f'{(booking.package.price if booking.package_id else booking.event.price) * booking.number_of_people:,.0f}',
        'fee_display': f'{booking.booking_fee:,.0f}',
        'total_display': f'{booking.total_price:,.0f}',
    })


    return render(request, 'bookings/checkout.html', {'booking': booking, 'form': form})
 
 
@login_required
def confirmation(request, reference):
    booking = get_object_or_404(Booking.objects.select_related('event', 'package'), reference=reference, user=request.user)
    return render(request, 'bookings/confirmation.html', {'booking': booking})
