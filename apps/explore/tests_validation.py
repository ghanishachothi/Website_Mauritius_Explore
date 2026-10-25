"""Tests for the validation rules added for FR-C05, C08, C09, C14, C16, V19 and A05.

Run with:  python manage.py test apps.explore.tests_validation
"""
from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .forms import CheckoutForm
from .models import Booking, Event, Review

User = get_user_model()


def make_event(title, days_from_today):
    return Event.objects.create(
        title=title,
        date=timezone.localdate() + timedelta(days=days_from_today),
        price=Decimal('500.00'),
    )


def make_booking(user, event, **extra):
    return Booking.objects.create(
        user=user, event=event, number_of_people=1,
        full_name='Test User', email='test@example.com', **extra,
    )


class ReviewRulesTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='reviewer', password='Sunny$Beach2026')
        self.client.force_login(self.user)
        self.past = make_event('Past Hike', -3)
        self.future = make_event('Future Hike', 5)

    def post_review(self, event, rating='5', comment='Great day'):
        return self.client.post(reverse('experiences:add_review'),
                                {'event': event.pk, 'rating': rating, 'comment': comment})

    def test_cannot_review_without_a_booking(self):
        self.post_review(self.past)
        self.assertEqual(Review.objects.count(), 0)

    def test_cannot_review_an_event_that_has_not_happened(self):
        make_booking(self.user, self.future)
        self.post_review(self.future)
        self.assertEqual(Review.objects.count(), 0)

    def test_cannot_review_after_cancelling_the_booking(self):
        make_booking(self.user, self.past, status=Booking.Status.CANCELLED)
        self.post_review(self.past)
        self.assertEqual(Review.objects.count(), 0)

    def test_can_review_a_completed_booked_event(self):
        make_booking(self.user, self.past)
        self.post_review(self.past)
        self.assertEqual(Review.objects.count(), 1)

    def test_rating_above_5_is_rejected(self):
        make_booking(self.user, self.past)
        self.post_review(self.past, rating='9')
        self.assertEqual(Review.objects.count(), 0)

    def test_rating_that_is_not_a_number_is_rejected_without_crashing(self):
        make_booking(self.user, self.past)
        response = self.post_review(self.past, rating='abc')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Review.objects.count(), 0)

    def test_edit_rejects_a_bad_rating_and_keeps_the_old_review(self):
        review = Review.objects.create(user=self.user, event=self.past, rating=4, comment='Nice')
        self.client.post(reverse('experiences:edit_review', args=[review.pk]),
                         {'rating': '12', 'comment': 'Changed'})
        review.refresh_from_db()
        self.assertEqual((review.rating, review.comment), (4, 'Nice'))

    def test_edit_saves_a_valid_review(self):
        review = Review.objects.create(user=self.user, event=self.past, rating=4, comment='Nice')
        self.client.post(reverse('experiences:edit_review', args=[review.pk]),
                         {'rating': '2', 'comment': 'Changed my mind'})
        review.refresh_from_db()
        self.assertEqual((review.rating, review.comment), (2, 'Changed my mind'))


class AccountRulesTests(TestCase):
    def signup(self, email, password='Sunny$Beach2026', name='Alex Doe'):
        return self.client.post(reverse('users:signup'), {
            'full_name': name, 'email': email, 'password1': password, 'password2': password,
        })

    def test_weak_password_is_rejected_at_signup(self):
        self.signup('weak@example.com', password='12345678')
        self.assertFalse(User.objects.filter(email='weak@example.com').exists())

    def test_strong_password_is_accepted_at_signup(self):
        self.signup('strong@example.com')
        self.assertTrue(User.objects.filter(email='strong@example.com').exists())

    def test_two_people_with_the_same_name_can_both_sign_up(self):
        self.signup('one@example.com')
        self.client.logout()
        self.signup('two@example.com')
        self.assertEqual(User.objects.filter(email__in=['one@example.com', 'two@example.com']).count(), 2)

    def test_profile_rejects_a_username_that_is_taken(self):
        User.objects.create_user(username='taken', password='Sunny$Beach2026')
        me = User.objects.create_user(username='me', email='me@example.com', password='Sunny$Beach2026')
        self.client.force_login(me)
        self.client.post(reverse('users:profile'), {
            'full_name': 'Me Myself', 'username': 'taken', 'email': 'me@example.com',
        })
        me.refresh_from_db()
        self.assertEqual(me.username, 'me')

    def test_profile_rejects_a_bad_phone_number(self):
        me = User.objects.create_user(username='me', email='me@example.com', password='Sunny$Beach2026')
        self.client.force_login(me)
        self.client.post(reverse('users:profile'), {
            'full_name': 'Me Myself', 'username': 'me', 'email': 'me@example.com',
            'phone_number': 'call me maybe',
        })
        me.refresh_from_db()
        self.assertEqual(me.profile.phone_number, '')

    def test_profile_saves_valid_changes(self):
        me = User.objects.create_user(username='me', email='me@example.com', password='Sunny$Beach2026')
        self.client.force_login(me)
        self.client.post(reverse('users:profile'), {
            'full_name': 'Me Myself', 'username': 'me2', 'email': 'me@example.com',
            'phone_number': '+230 5123 4567',
        })
        me.refresh_from_db()
        self.assertEqual(me.username, 'me2')
        self.assertEqual(me.profile.phone_number, '+230 5123 4567')


class PriceAndPaymentRulesTests(TestCase):
    def test_negative_event_price_is_invalid(self):
        event = Event(title='Bad price', date=timezone.localdate(), price=Decimal('-5.00'))
        with self.assertRaises(ValidationError) as caught:
            event.full_clean()
        self.assertIn('price', caught.exception.message_dict)

    def test_expired_card_is_rejected(self):
        user = User.objects.create_user(username='payer', password='Sunny$Beach2026')
        booking = make_booking(user, make_event('Cruise', 5))
        form = CheckoutForm({
            'full_name': 'Test User', 'email': 'test@example.com', 'phone': '',
            'method': 'card', 'cardholder_name': 'Test User',
            'card_number': '4242424242424242', 'expiry': '01/20', 'cvv': '123',
        }, booking=booking)
        self.assertFalse(form.is_valid())
        self.assertIn('expiry', form.errors)

    def test_card_that_expires_in_the_future_is_accepted(self):
        user = User.objects.create_user(username='payer2', password='Sunny$Beach2026')
        booking = make_booking(user, make_event('Cruise 2', 5))
        year = (timezone.localdate().year + 2) % 100
        form = CheckoutForm({
            'full_name': 'Test User', 'email': 'test@example.com', 'phone': '',
            'method': 'card', 'cardholder_name': 'Test User',
            'card_number': '4242424242424242', 'expiry': '12/%02d' % year, 'cvv': '123',
        }, booking=booking)
        self.assertTrue(form.is_valid(), form.errors)
