from datetime import time, timedelta
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from .models import Category, Event
from .models import Destination, Region
from datetime import timedelta


# ======================================================================
# from the old "destinations" app
# ======================================================================

class ExploreIslandTests(TestCase):

    def setUp(self):
        # These pages are for logged-in users only, so log a test user in.
        user = get_user_model().objects.create_user(username='tester', password='pass12345')
        self.client.force_login(user)
    @classmethod
    def setUpTestData(cls):
        cls.north, _ = Region.objects.get_or_create(name='North', defaults={'slug': 'north'})
        cls.south, _ = Region.objects.get_or_create(name='South', defaults={'slug': 'south'})
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

    def test_explore_route_keeps_the_region_hub_and_links_to_explore_your_way(self):
        response = self.client.get(reverse('destinations:explore_island'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'PLAN YOUR ISLAND ADVENTURE')
        self.assertContains(response, reverse('experiences:explore_your_way'))
        self.assertNotContains(response, 'href=""')

    def test_experience_finder_uses_the_shared_events_and_destination_data(self):
        response = self.client.get(reverse('destinations:experience_finder'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Catamaran Cruise')
        self.assertContains(response, 'Blue Bay Snorkelling')
        self.assertContains(response, 'Chamarel Waterfall')
        self.assertContains(response, 'class="eb-navbar"')
        self.assertContains(response, 'images/logo.png')
        self.assertNotContains(response, 'Past Island Walk')
        self.assertEqual(response.context['result_count'], 3)
        self.assertEqual(len(response.context['map_points']), 3)

    def test_category_location_difficulty_and_price_filters_combine(self):
        response = self.client.get(reverse('destinations:experience_finder'), {
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
        response = self.client.get(reverse('destinations:experience_finder'), {'duration': 'full-day'})

        self.assertEqual(
            [result['name'] for result in response.context['results']],
            ['Catamaran Cruise'],
        )
        self.assertContains(response, 'Full day')

    def test_several_duration_filters_can_be_selected_at_once(self):
        response = self.client.get(reverse('destinations:experience_finder'), {
            'duration': ['under-2', 'full-day'],
        })

        self.assertEqual(
            {result['name'] for result in response.context['results']},
            {'Catamaran Cruise', 'Chamarel Waterfall'},
        )

    def test_search_matches_title_and_location(self):
        title_response = self.client.get(reverse('destinations:experience_finder'), {'q': 'snorkelling'})
        location_response = self.client.get(reverse('destinations:experience_finder'), {'location': 'East Coast'})

        self.assertEqual(
            [result['name'] for result in title_response.context['results']],
            ['Blue Bay Snorkelling'],
        )
        self.assertEqual(
            [result['name'] for result in location_response.context['results']],
            ['Catamaran Cruise'],
        )

    def test_price_sort_orders_experiences_low_to_high(self):
        response = self.client.get(reverse('destinations:experience_finder'), {'sort': 'price_low'})

        self.assertEqual(
            [result['name'] for result in response.context['results']],
            ['Blue Bay Snorkelling', 'Chamarel Waterfall', 'Catamaran Cruise'],
        )

    def test_malformed_prices_show_validation_errors(self):
        response = self.client.get(reverse('destinations:experience_finder'), {
            'min_price': 'a-lot',
            'max_price': '-3',
        })

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['filter_errors']), 2)
        self.assertContains(response, 'Enter a valid minimum price.')
        self.assertContains(response, 'Maximum price must be zero or more.')

    def test_legacy_explore_route_and_experience_links_remain_available(self):
        hub_response = self.client.get(reverse('destinations:explore_island'))
        finder_response = self.client.get(reverse('destinations:experience_finder'))
        local_experiences_response = self.client.get(reverse('explore'))
        event_response = self.client.get(self.sailing.get_absolute_url())

        self.assertEqual(hub_response.status_code, 200)
        self.assertContains(hub_response, 'PLAN YOUR ISLAND ADVENTURE')
        self.assertEqual(finder_response.status_code, 200)
        self.assertContains(finder_response, 'EXPLORE EXPERIENCES')
        self.assertEqual(local_experiences_response.status_code, 200)
        self.assertContains(local_experiences_response, 'Local Experiences')
        self.assertEqual(event_response.status_code, 200)

    def test_navigation_routes_used_by_the_explore_frame_resolve(self):
        for route in (
            'core:home',
            'explore',
            'explore_island',
            'destinations:experience_finder',
            'experiences:all_events',
            'experiences:my_experiences',
            'users:profile',
            'admin:login',
            'core:contact',
        ):
            with self.subTest(route=route):
                self.assertTrue(reverse(route))


class LocalExperiencesTests(TestCase):

    def setUp(self):
        # These pages are for logged-in users only, so log a test user in.
        user = get_user_model().objects.create_user(username='tester', password='pass12345')
        self.client.force_login(user)
    @classmethod
    def setUpTestData(cls):
        cls.region, _ = Region.objects.get_or_create(name='North', defaults={'slug': 'north'})
        cls.destination = Destination.objects.create(
            name='Port Louis', slug='port-louis', region=cls.region
        )
        cls.guided_tours = Category.objects.create(name='Guided Tours', slug='guided-tours')
        cls.waterfalls = Category.objects.create(name='Waterfalls', slug='waterfalls')
        cls.workshop = Event.objects.create(
            title='Traditional Craft Workshop',
            date=timezone.localdate() + timedelta(days=5),
            location_name='Port Louis',
            category=cls.guided_tours,
            destination=cls.destination,
            price=Decimal('950.00'),
            rating=Decimal('4.8'),
            start_time=time(10),
            end_time=time(12),
        )
        cls.waterfall = Event.objects.create(
            title='Chamarel Waterfall Walk',
            date=timezone.localdate() + timedelta(days=7),
            category=cls.waterfalls,
            price=Decimal('1200.00'),
        )

    def test_local_experiences_page_renders_shared_database_cards_and_categories(self):
        response = self.client.get(reverse('explore'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.workshop.title)
        self.assertContains(response, 'Port Louis')
        self.assertContains(response, 'Rs 950')
        self.assertContains(response, 'Guided Tours')
        self.assertContains(response, 'Waterfalls')
        self.assertEqual(response.context['cards'][0]['event'], self.workshop)

    def test_search_filters_by_experience_and_place(self):
        response = self.client.get(reverse('explore'), {'q': 'Port Louis'})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.workshop.title)
        self.assertNotContains(response, self.waterfall.title)

    def test_category_filter_uses_database_category_slug(self):
        response = self.client.get(reverse('explore'), {'category': 'waterfalls'})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.waterfall.title)
        self.assertNotContains(response, self.workshop.title)

    def test_search_with_no_matches_shows_clear_empty_state(self):
        response = self.client.get(reverse('explore'), {'q': 'no such activity'})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'No local experiences found')


class RegionShowcaseTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.east, _ = Region.objects.get_or_create(name='East', defaults={'slug': 'east'})
        cls.west, _ = Region.objects.get_or_create(name='West', defaults={'slug': 'west'})

    def test_region_absolute_url_uses_the_regions_route_and_legacy_route_remains(self):
        self.assertEqual(self.east.get_absolute_url(), '/destinations/region/east/')
        region_response = self.client.get(reverse('destinations:region_detail', args=['east']))
        legacy_response = self.client.get(reverse('region_showcase', args=['east']))
        self.assertEqual(region_response.status_code, 200)
        self.assertContains(region_response, 'class="eb-navbar"')
        self.assertContains(region_response, 'images/logo.png')
        self.assertEqual(legacy_response.status_code, 200)

    def test_region_showcase_has_useful_empty_states(self):
        Region.objects.create(name='Central Test', slug='central-test')
        response = self.client.get(reverse('region_showcase', args=['central-test']))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'No places added yet.')
        self.assertContains(response, 'About the Central Test')
        self.assertContains(response, 'Central Test Highlights')


# ======================================================================
# from the old "experiences" app
# ======================================================================

class ExperiencePageTests(TestCase):

    def setUp(self):
        # These pages are for logged-in users only, so log a test user in.
        user = get_user_model().objects.create_user(username='tester', password='pass12345')
        self.client.force_login(user)
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
        explore_url = reverse('experiences:explore_your_way')
        self.assertContains(response, f'<a href="{explore_url}">Experiences</a>')
        self.assertContains(response, f'<a href="{explore_url}">All Experiences</a>')
        self.assertContains(response, reverse('bookings:reserve', args=[self.event.slug]))

    def test_gallery_hides_thumbnail_strip_for_single_photo(self):
        event = Event.objects.create(
            title='One Photo Tour',
            date=timezone.localdate() + timedelta(days=8),
            price='700.00',
            destination=self.destination,
            category=self.category,
            image='events/one-photo.jpg',
        )

        response = self.client.get(reverse('experiences:event_detail', args=[event.slug]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id="main-gallery-img"')
        self.assertContains(response, 'experience-gallery no-thumbnails')
        self.assertNotContains(response, 'class="experience-thumbnails"')

    def test_gallery_shows_one_thumbnail_per_extra_photo(self):
        event = Event.objects.create(
            title='Three Photo Tour',
            date=timezone.localdate() + timedelta(days=9),
            price='800.00',
            destination=self.destination,
            category=self.category,
            image='events/main.jpg',
            gallery_image_1='events/gallery/one.jpg',
            gallery_image_2='events/gallery/two.jpg',
        )

        response = self.client.get(reverse('experiences:event_detail', args=[event.slug]))

        self.assertContains(response, 'class="experience-thumbnails"')
        self.assertNotContains(response, 'no-thumbnails')
        self.assertEqual(response.content.decode().count('class="gallery-thumb'), 2)
        self.assertContains(response, 'class="gallery-thumb is-active"')

    def test_gallery_without_photos_shows_placeholder_and_no_thumbnails(self):
        response = self.client.get(reverse('experiences:event_detail', args=[self.event.slug]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'image-placeholder')
        self.assertContains(response, 'experience-gallery no-thumbnails')
        self.assertNotContains(response, 'class="experience-thumbnails"')

    def test_unknown_slug_returns_404(self):
        response = self.client.get(reverse('experiences:event_detail', args=['not-an-event']))

        self.assertEqual(response.status_code, 404)

    def test_event_detail_has_back_link_to_explore_your_way(self):
        response = self.client.get(reverse('experiences:event_detail', args=[self.event.slug]))

        self.assertContains(response, 'experience-back-link')
        self.assertContains(response, 'Back to Explore Your Way')
        self.assertContains(response, reverse('experiences:explore_your_way'))

    def test_navigation_shows_explore_your_way_once(self):
        response = self.client.get(reverse('experiences:explore_your_way'))

        self.assertEqual(response.content.count(b'>Explore your Way</a>'), 1)
        self.assertNotContains(response, 'Experience Insight')

    def test_experience_insight_redirects_to_explore_your_way(self):
        response = self.client.get(reverse('experiences:experience_insight'))

        self.assertRedirects(response, reverse('experiences:explore_your_way'))

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

    def test_explore_your_way_filters_events_by_max_price(self):
        self.client.force_login(get_user_model().objects.create_user(username='price-filter-user'))
        cheap_event = Event.objects.create(
            title='Affordable Lagoon Tour',
            date=timezone.localdate() + timedelta(days=6),
            price='500.00',
            destination=self.destination,
            category=self.category,
        )
        expensive_event = Event.objects.create(
            title='Luxury Lagoon Tour',
            date=timezone.localdate() + timedelta(days=7),
            price='1500.00',
            destination=self.destination,
            category=self.category,
        )

        url = reverse('experiences:explore_your_way')
        default_response = self.client.get(url)

        self.assertContains(default_response, 'value="10000"')
        self.assertContains(default_response, 'Rs 10,000')

        response = self.client.get(url, {'max_price': '1000'})

        self.assertEqual(response.status_code, 200)
        self.assertEqual([event.pk for event in response.context['events']], [cheap_event.pk])
        self.assertNotContains(response, expensive_event.title)
        self.assertContains(response, 'Rs 1,000')

    def test_explore_your_way_empty_state_for_nonmatching_query(self):
        response = self.client.get(reverse('experiences:explore_your_way'), {'q': 'mountain'})

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, self.event.title)
        self.assertContains(response, 'No experiences match')