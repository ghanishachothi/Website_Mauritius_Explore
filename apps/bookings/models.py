import secrets

from django.conf import settings
from django.db import models


def generate_reference():
    return 'ME-' + secrets.token_hex(3).upper()


class Booking(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending payment'
        CONFIRMED = 'confirmed', 'Confirmed'
        CANCELLED = 'cancelled', 'Cancelled'

    reference = models.CharField(max_length=12, unique=True, default=generate_reference, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='bookings')
    event = models.ForeignKey('experiences.Event', on_delete=models.PROTECT, related_name='bookings')
    number_of_people = models.PositiveIntegerField(default=1)
    full_name = models.CharField(max_length=150)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True)
    special_requests = models.TextField(blank=True)
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    booking_fee = models.DecimalField(max_digits=10, decimal_places=2, default=50,
    help_text='Flat fee added once per booking (Rs)')
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        self.total_price = self.event.price * self.number_of_people + self.booking_fee
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.reference} - {self.event.title} ({self.user.username})'


class Payment(models.Model):
    # DEMO ONLY: we never store full card numbers or CVV, only the last 4 digits.
    class Method(models.TextChoices):
        JUICE = 'juice', 'JUICE by MCB'
        CARD = 'card', 'Credit Card (Visa/Mastercard)'
        MYT = 'myt', 'My.T Money'
        QR = 'qr', 'Scan to Pay'

    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        PAID = 'paid', 'Paid'
        FAILED = 'failed', 'Failed'

    booking = models.OneToOneField(Booking, on_delete=models.CASCADE, related_name='payment')
    method = models.CharField(max_length=10, choices=Method.choices)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    card_last4 = models.CharField(max_length=4, blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f'{self.booking.reference} - {self.get_status_display()}'

