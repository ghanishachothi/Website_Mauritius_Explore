from datetime import time, timedelta
from decimal import Decimal
from io import StringIO

from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.experiences.models import Category, Event

from .models import Destination, Guide, Package, Region


class ExploreIslandTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.north = Region.objects.create(name='North', slug='north')
        cls.south = Region.objects.create(name='South', slug='south')
        cls.blue_bay = Destination.objects.create(
            region=cls.north,
            name='Blue Bay',
            slug='blue-bay',
            latitude=Decimal('-20.02'),
            longitude=Decimal('57.58'),
        )
        cls.chamarel = Destination.objects.create(
            region=cls.south,
            name='Chamarel',
            slug='chamarel',
            latitude=Decimal('-20.42'),
            longitude=Decimal('57.45'),
        )
        cls.nature = Category.objects.create(name='Nature', slug='nature', icon='🌿')
        cls.water = Category.objects.create(name='Water Sports', slug='water-sports', icon='⛵')
        today = timezone.localdate()
        cls.sailing = Event.objects.create(
            title='Catamaran Cruise',
            slug='catamaran-cruise',
            category=cls.water,
            destination=cls.blue_bay,
            location_name='East Coast',
            date=today + timedelta(days=2),
            start_time=time(9),
            end_time=time(17),
            price=Decimal('2500.00'),
            difficulty='easy',
            is_featured=True,
        )
        cls.snorkelling = Event.objects.create(
            title='Blue Bay Snorkelling',
            slug='blue-bay-snorkelling',
            category=cls.water,
            destination=cls.blue_bay,
            location_name='South East',
            date=today + timedelta(days=4),
            start_time=time(9),
            end_time=time(12),
            price=Decimal('1800.00'),
            difficulty='moderate',
        )
        cls.waterfall = Event.objects.create(
            title='Chamarel Waterfall',
            slug='chamarel-waterfall',
            category=cls.nature,
            destination=cls.chamarel,
            location_name='South West',
            date=today + timedelta(days=6),
            start_time=time(10),
            end_time=time(12),
            price=Decimal('2200.00'),
            difficulty='challenging',
        )
        Event.objects.create(
            title='Past Island Walk',
            slug='past-island-walk',
            category=cls.nature,
            destination=cls.chamarel,
            date=today - timedelta(days=1),
            price=Decimal('300.00'),
        )

    def test_explore_route_uses_the_shared_events_and_destination_data(self):
        response = self.client.get(reverse('explore'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Catamaran Cruise')
        self.assertContains(response, 'Blue Bay Snorkelling')
        self.assertContains(response, 'Chamarel Waterfall')
        self.assertNotContains(response, 'Past Island Walk')
        self.assertEqual(response.context['result_count'], 3)
        self.assertEqual(len(response.context['map_points']), 3)

    def test_category_location_difficulty_and_price_filters_combine(self):
        response = self.client.get(reverse('explore'), {
            'category': 'water-sports',
            'region': 'north',
            'difficulty': 'moderate',
            'min_price': '1000',
            'max_price': '2000',
        })

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            [result['name'] for result in response.context['results']],
            ['Blue Bay Snorkelling'],
        )

    def test_duration_filter_uses_start_and_end_times(self):
        response = self.client.get(reverse('explore'), {'duration': 'full-day'})

        self.assertEqual(
            [result['name'] for result in response.context['results']],
            ['Catamaran Cruise'],
        )
        self.assertContains(response, 'Full day')

    def test_several_duration_filters_can_be_selected_at_once(self):
        response = self.client.get(reverse('explore'), {
            'duration': ['under-2', 'full-day'],
        })

        self.assertEqual(
            {result['name'] for result in response.context['results']},
            {'Catamaran Cruise', 'Chamarel Waterfall'},
        )

    def test_search_matches_title_and_location(self):
        title_response = self.client.get(reverse('explore'), {'q': 'snorkelling'})
        location_response = self.client.get(reverse('explore'), {'location': 'East Coast'})

        self.assertEqual(
            [result['name'] for result in title_response.context['results']],
            ['Blue Bay Snorkelling'],
        )
        self.assertEqual(
            [result['name'] for result in location_response.context['results']],
            ['Catamaran Cruise'],
        )

    def test_price_sort_orders_experiences_low_to_high(self):
        response = self.client.get(reverse('explore'), {'sort': 'price_low'})

        self.assertEqual(
            [result['name'] for result in response.context['results']],
            ['Blue Bay Snorkelling', 'Chamarel Waterfall', 'Catamaran Cruise'],
        )

    def test_malformed_prices_show_validation_errors(self):
        response = self.client.get(reverse('explore'), {
            'min_price': 'a-lot',
            'max_price': '-3',
        })

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['filter_errors']), 2)
        self.assertContains(response, 'Enter a valid minimum price.')
        self.assertContains(response, 'Maximum price must be zero or more.')

    def test_legacy_explore_route_and_experience_links_remain_available(self):
        legacy_response = self.client.get(reverse('destinations:explore_island'))
        event_response = self.client.get(self.sailing.get_absolute_url())

        self.assertEqual(legacy_response.status_code, 200)
        self.assertContains(legacy_response, 'EXPLORE EXPERIENCES')
        self.assertEqual(event_response.status_code, 200)

    def test_navigation_routes_used_by_the_explore_frame_resolve(self):
        for route in (
            'core:home',
            'experiences:all_events',
            'experiences:my_experiences',
            'users:profile',
            'admin:login',
            'core:contact',
        ):
            with self.subTest(route=route):
                self.assertTrue(reverse(route))


class RegionShowcaseTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.east = Region.objects.create(
            name='East',
            slug='east',
            tagline='Lagoons, island adventures and the easy rhythm of the east coast.',
            description='Explore the eastern shoreline.',
        )
        cls.west = Region.objects.create(name='West', slug='west')
        cls.ile_aux_cerfs = Destination.objects.create(
            region=cls.east,
            name='Ile aux Cerfs',
            slug='ile-aux-cerfs',
            short_description='A lagoon island reached by boat from the east coast.',
        )
        cls.le_morne = Destination.objects.create(
            region=cls.west,
            name='Le Morne',
            slug='le-morne',
        )
        cls.east_guide = Guide.objects.create(
            name='East Coast Guide',
            slug='east-coast-guide',
            languages='English, French',
        )
        cls.east_package = Package.objects.create(
            title='East Coast Lagoon Day',
            slug='east-coast-lagoon-day',
            guide=cls.east_guide,
            description='A guided day exploring the east coast lagoon.',
            price=Decimal('4200.00'),
            duration='Full day',
        )
        cls.east_package.destinations.add(cls.ile_aux_cerfs)
        cls.west_guide = Guide.objects.create(name='West Coast Guide', slug='west-coast-guide')
        cls.west_package = Package.objects.create(
            title='West Coast Hike',
            slug='west-coast-hike',
            guide=cls.west_guide,
            price=Decimal('3000.00'),
        )
        cls.west_package.destinations.add(cls.le_morne)
        Event.objects.create(
            title='East Lagoon Cruise',
            slug='east-lagoon-cruise',
            destination=cls.ile_aux_cerfs,
            date=timezone.localdate() + timedelta(days=4),
            price=Decimal('1800.00'),
        )

    def test_east_showcase_route_renders_region_attractions_packages_guides_and_events(self):
        response = self.client.get(reverse('region_showcase', args=['east']))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'East Mauritius')
        self.assertContains(response, 'Ile aux Cerfs')
        self.assertContains(response, 'East Coast Lagoon Day')
        self.assertContains(response, 'East Coast Guide')
        self.assertContains(response, 'East Lagoon Cruise')
        self.assertNotContains(response, 'West Coast Hike')
        self.assertEqual(response.context['packages'].count(), 1)
        self.assertEqual(response.context['guides'].count(), 1)

    def test_region_absolute_url_uses_the_regions_route_and_legacy_route_remains(self):
        self.assertEqual(self.east.get_absolute_url(), '/regions/east/')
        response = self.client.get(reverse('destinations:region_detail', args=['east']))
        self.assertEqual(response.status_code, 200)

    def test_region_showcase_has_useful_empty_states(self):
        Region.objects.create(name='Central', slug='central')
        response = self.client.get(reverse('region_showcase', args=['central']))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Places to discover')
        self.assertContains(response, 'Packages &amp; local guides')
        self.assertContains(response, 'Upcoming in the Central')
        self.assertContains(response, 'More places are on their way')
        self.assertContains(response, 'Local packages coming soon')

    def test_east_showcase_keeps_the_supplied_design_and_live_destination_links(self):
        response = self.client.get(reverse('region_showcase', args=['east']))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'east/hero-east-sunset.jpg')
        self.assertContains(response, 'Where the ocean')
        self.assertContains(response, 'Discover the Best of the East')
        self.assertContains(response, 'East Highlights')
        self.assertContains(response, '/destinations/place/ile-aux-cerfs/')
        self.assertContains(response, '/destinations/guides-packages/?region=east')
        self.assertContains(response, '/destinations/guides/east-coast-guide/')

        catalog_response = self.client.get(reverse('destinations:guides_packages'), {'region': 'east'})
        self.assertEqual(catalog_response.status_code, 200)
        self.assertContains(catalog_response, 'East Coast Lagoon Day')
        self.assertContains(catalog_response, 'East Coast Guide')
        self.assertNotContains(catalog_response, 'West Coast Hike')
        self.assertNotContains(catalog_response, 'West Coast Guide')


class EastRegionDemoContentTests(TestCase):
    def test_demo_seed_populates_linkable_east_places_and_local_package(self):
        call_command('seed_demo', stdout=StringIO())
        call_command('seed_demo', stdout=StringIO())

        east = Region.objects.get(slug='east')
        expected_places = {
            'Ile aux Cerfs',
            'Belle Mare',
            'GRSE Waterfall',
            'Poste de Flacq Temple',
            'Bras d’Eau',
            'Trou d’Eau Douce Lagoon',
        }
        self.assertSetEqual(
            set(east.destinations.values_list('name', flat=True)),
            expected_places,
        )
        east_packages = Package.objects.filter(destinations__region=east).distinct()
        self.assertEqual(east_packages.count(), 1)
        self.assertEqual(east_packages.first().destinations.count(), 3)

        response = self.client.get(east.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        for place in expected_places:
            with self.subTest(place=place):
                self.assertContains(response, place)
        self.assertEqual(
            [destination.slug for destination in response.context['destinations']],
            [
                'ile-aux-cerfs',
                'belle-mare',
                'grse-waterfall',
                'poste-de-flacq-temple',
                'bras-deau',
                'trou-deau-douce-lagoon',
            ],
        )
        self.assertContains(response, 'East Coast Lagoon Day')
        self.assertContains(response, 'Meet East Coast Guide')
