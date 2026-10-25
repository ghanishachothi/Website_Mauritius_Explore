"""Tests for the two requirements that were not started:
FR-A10 (admin rejects booking requests, with FR-A09 accept) and FR-A06 (guide availability).

Run with:  python manage.py test apps.explore.tests_not_started
"""
from datetime import time, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .forms import ReservePackageForm
from .models import Booking, Event, Guide, GuideUnavailability, Package

User = get_user_model()


def make_event(title='Cruise', days=5, **extra):
    return Event.objects.create(title=title, date=timezone.localdate() + timedelta(days=days),
                                price=Decimal('500.00'), **extra)


def make_booking(user, event, **extra):
    return Booking.objects.create(user=user, event=event, number_of_people=1,
                                  full_name='Test User', email='test@example.com', **extra)


class RejectBookingTests(TestCase):
    """FR-A09 and FR-A10."""

    def setUp(self):
        self.admin = User.objects.create_superuser('boss', 'boss@example.com', 'Pass12345!')
        self.customer = User.objects.create_user('cust', password='Pass12345!')
        self.booking = make_booking(self.customer, make_event())
        self.client.force_login(self.admin)

    def run_action(self, action):
        return self.client.post(reverse('admin:explore_booking_changelist'), {
            'action': action, '_selected_action': [self.booking.pk],
        }, follow=True)

    def test_admin_can_reject_a_booking(self):
        self.run_action('reject_bookings')
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.status, Booking.Status.REJECTED)

    def test_admin_can_accept_a_booking(self):
        self.run_action('accept_bookings')
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.status, Booking.Status.CONFIRMED)

    def test_a_cancelled_booking_cannot_be_accepted(self):
        self.booking.status = Booking.Status.CANCELLED
        self.booking.save()
        self.run_action('accept_bookings')
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.status, Booking.Status.CANCELLED)

    def test_a_rejected_booking_cannot_be_accepted(self):
        self.booking.status = Booking.Status.REJECTED
        self.booking.save()
        self.run_action('accept_bookings')
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.status, Booking.Status.REJECTED)

    def test_rejected_booking_frees_its_spots(self):
        event = make_event('Small tour', capacity=2)
        booking = make_booking(self.customer, event)
        self.assertEqual(event.spots_left, 1)
        booking.status = Booking.Status.REJECTED
        booking.save()
        self.assertEqual(event.spots_left, 2)

    def test_rejected_booking_cannot_be_paid(self):
        self.booking.status = Booking.Status.REJECTED
        self.booking.save()
        self.client.force_login(self.customer)
        response = self.client.get(reverse('bookings:checkout', args=[self.booking.reference]))
        self.assertRedirects(response, reverse('experiences:my_experiences'),
                             fetch_redirect_response=False)

    def test_customer_sees_rejected_status_without_a_cancel_button(self):
        self.booking.status = Booking.Status.REJECTED
        self.booking.save()
        self.client.force_login(self.customer)
        response = self.client.get(reverse('experiences:my_experiences'))
        self.assertContains(response, 'Rejected')
        self.assertNotContains(response, reverse('experiences:cancel_booking', args=[self.booking.pk]))


class GuideAvailabilityTests(TestCase):
    """FR-A06."""

    def test_guide_is_unavailable_only_inside_the_blocked_period(self):
        guide = Guide.objects.create(name='Test Guide')
        start = timezone.localdate() + timedelta(days=10)
        GuideUnavailability.objects.create(guide=guide, start_date=start, end_date=start + timedelta(days=2))
        self.assertTrue(guide.is_available_on(start - timedelta(days=1)))
        self.assertFalse(guide.is_available_on(start))
        self.assertFalse(guide.is_available_on(start + timedelta(days=2)))
        self.assertTrue(guide.is_available_on(start + timedelta(days=3)))

    def test_inactive_guide_is_never_available(self):
        guide = Guide.objects.create(name='Retired Guide', is_active=False)
        self.assertFalse(guide.is_available_on(timezone.localdate()))

    def test_end_date_before_start_date_is_invalid(self):
        guide = Guide.objects.create(name='Date Guide')
        today = timezone.localdate()
        period = GuideUnavailability(guide=guide, start_date=today, end_date=today - timedelta(days=1))
        with self.assertRaises(ValidationError):
            period.full_clean()

    def test_booking_form_refuses_a_guide_who_is_unavailable(self):
        guide = Guide.objects.create(name='Busy Guide')
        package = Package.objects.create(title='Reef Trip', price='900.00', guide=guide, max_people=10)
        day = timezone.localdate() + timedelta(days=7)
        GuideUnavailability.objects.create(guide=guide, start_date=day, end_date=day)
        data = {
            'preferred_date': day.isoformat(), 'number_of_people': 2, 'guide': guide.pk,
            'full_name': 'Test User', 'email': 'test@example.com', 'phone': '',
            'preferred_time': time(10, 0).strftime('%H:%M'), 'agree': 'on',
        }
        form = ReservePackageForm(data, package=package)
        self.assertFalse(form.is_valid())
        self.assertIn('guide', form.errors)

    def test_booking_form_accepts_the_same_guide_on_a_free_day(self):
        guide = Guide.objects.create(name='Free Guide')
        package = Package.objects.create(title='Reef Trip 2', price='900.00', guide=guide, max_people=10)
        day = timezone.localdate() + timedelta(days=7)
        GuideUnavailability.objects.create(guide=guide, start_date=day, end_date=day)
        free_day = day + timedelta(days=1)
        data = {
            'preferred_date': free_day.isoformat(), 'number_of_people': 2, 'guide': guide.pk,
            'full_name': 'Test User', 'email': 'test@example.com', 'phone': '',
            'preferred_time': time(10, 0).strftime('%H:%M'), 'agree': 'on',
        }
        form = ReservePackageForm(data, package=package)
        self.assertTrue(form.is_valid(), form.errors)
