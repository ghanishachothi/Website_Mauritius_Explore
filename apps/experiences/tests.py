from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.destinations.models import Destination, Region

from .models import Category, Event


class ExperiencePageTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.region = Region.objects.create(name='East')
        cls.destination = Destination.objects.create(name='Belle Mare', region=cls.region)
        cls.category = Category.objects.create(name='Water Sports')
        cls.event = Event.objects.create(
            title='Lagoon Snorkelling',
            date=timezone.localdate() + timedelta(days=5),
            price='1250.00',
            description='Explore the East Coast lagoon.',
            destination=cls.destination,
            category=cls.category,
        )

    def test_slug_detail_uses_database_event(self):
        response = self.client.get(reverse('experiences:event_detail', args=[self.event.slug]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.event.title)
        self.assertContains(response, 'page-breadcrumbs')
        self.assertContains(response, reverse('experiences:experience_insight'))
        self.assertContains(response, reverse('experiences:explore_your_way'))
        self.assertContains(response, reverse('bookings:reserve', args=[self.event.slug]))

    def test_unknown_slug_returns_404(self):
        response = self.client.get(reverse('experiences:event_detail', args=['not-an-event']))

        self.assertEqual(response.status_code, 404)

    def test_explore_your_way_filters_database_events(self):
        response = self.client.get(reverse('experiences:explore_your_way'), {
            'q': 'lagoon',
            'category': self.category.slug,
        })

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.event.title)
        self.assertNotContains(response, 'No experiences match')

    def test_explore_your_way_empty_state_for_nonmatching_query(self):
        response = self.client.get(reverse('experiences:explore_your_way'), {'q': 'mountain'})

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, self.event.title)
        self.assertContains(response, 'No experiences match')