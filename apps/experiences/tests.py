from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.destinations.models import Destination, Region

from .models import Category, Event


class ExperiencePageTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.region, _ = Region.objects.get_or_create(name='East', defaults={'slug': 'east'})
        cls.destination, _ = Destination.objects.get_or_create(
            name='Belle Mare', defaults={'region': cls.region}
        )
        cls.category = Category.objects.create(name='Water Sports')
        for order, name in enumerate((
            'Nature',
            'Culture',
            'Heritage and History',
            'Food and Drinks',
            'Local Experiences',
        )):
            Category.objects.get_or_create(name=name, defaults={'order': order})
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

    def test_experience_insight_uses_its_own_heading_and_shared_navigation(self):
        event = Event.objects.create(
            title='Catamaran Cruise to Ile Aux Cerfs',
            slug='ile-aux-cerfs-catamaran-day',
            date=timezone.localdate() + timedelta(days=8),
            price='2500.00',
            premium_price='3500.00',
            description='Sail across the East Coast lagoon.',
            destination=self.destination,
            category=self.category,
        )
        response = self.client.get(reverse('experiences:experience_insight'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, event.title)
        self.assertContains(response, 'Package Options')
        self.assertContains(response, reverse('bookings:reserve', args=[event.slug]))
        self.assertContains(response, reverse('experiences:explore_your_way'))
        self.assertContains(response, 'class="eb-navbar"')
        self.assertContains(response, 'images/logo.png')

    def test_explore_your_way_shows_design_categories_in_order_with_icons(self):
        response = self.client.get(reverse('experiences:explore_your_way'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            [category.name for category in response.context['categories']],
            ['Nature', 'Culture', 'Heritage and History', 'Food and Drinks', 'Local Experiences'],
        )
        self.assertEqual(
            [category.icon_class for category in response.context['categories']],
            [
                'fa-solid fa-mountain-sun',
                'fa-solid fa-masks-theater',
                'fa-solid fa-landmark',
                'fa-solid fa-utensils',
                'fa-solid fa-person-hiking',
            ],
        )
        self.assertContains(response, reverse('experiences:event_detail', args=[self.event.slug]))

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