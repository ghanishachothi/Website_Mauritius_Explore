from datetime import time, timedelta
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from .models import Category, Event
from .models import Destination, Region
from datetime import timedelta
from .models import Booking, Package, Payment, Profile, Review


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
            show_on_explore_your_way=True,
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

    def test_related_experience_links_are_marked_as_related(self):
        other = Event.objects.create(
            title='Reef Walk',
            date=timezone.localdate() + timedelta(days=10),
            price='400.00',
            destination=self.destination,
            category=self.category,
        )

        response = self.client.get(reverse('experiences:event_detail', args=[self.event.slug]))

        self.assertContains(response, 'You might also like')
        self.assertContains(response, f'href="{other.get_absolute_url()}?via=related"')

    def test_back_link_falls_back_to_explore_your_way(self):
        response = self.client.get(reverse('experiences:event_detail', args=[self.event.slug]))

        explore_url = reverse('experiences:explore_your_way')
        self.assertContains(response, f'id="expBack" href="{explore_url}"')
        self.assertContains(response, 'Back to Explore Your Way')

    def test_explore_your_way_hides_events_not_marked_for_it(self):
        hidden = Event.objects.create(
            title='Calendar Only Evening',
            date=timezone.localdate() + timedelta(days=11),
            price='300.00',
            destination=self.destination,
            category=self.category,
        )

        response = self.client.get(reverse('experiences:explore_your_way'))

        self.assertContains(response, self.event.title)
        self.assertNotContains(response, hidden.title)
        self.assertNotIn(hidden.pk, [event.pk for event in response.context['events']])

    def test_new_events_are_not_on_explore_your_way_by_default(self):
        event = Event.objects.create(
            title='Default Flag Walk',
            date=timezone.localdate() + timedelta(days=12),
            price='250.00',
            destination=self.destination,
            category=self.category,
        )

        self.assertFalse(event.show_on_explore_your_way)

    def test_explore_board_recommended_only_shows_flagged_events(self):
        shown = Event.objects.create(
            title='Board Sunset Sail',
            date=timezone.localdate() + timedelta(days=13),
            price='700.00',
            destination=self.destination,
            category=self.category,
            show_on_explore_board=True,
        )
        hidden = Event.objects.create(
            title='Board Hidden Trek',
            date=timezone.localdate() + timedelta(days=14),
            price='650.00',
            destination=self.destination,
            category=self.category,
        )

        response = self.client.get(reverse('destinations:explore_board'))

        slugs = [item['slug'] for item in response.context['recommended']]
        self.assertIn(shown.slug, slugs)
        self.assertNotIn(hidden.slug, slugs)

    def test_new_events_are_not_on_explore_board_by_default(self):
        event = Event.objects.create(
            title='Board Default Walk',
            date=timezone.localdate() + timedelta(days=15),
            price='200.00',
            destination=self.destination,
            category=self.category,
        )

        self.assertFalse(event.show_on_explore_board)

    def test_all_events_page_only_shows_flagged_events(self):
        shown = Event.objects.create(
            title='All Events Kayak Day',
            date=timezone.localdate() + timedelta(days=16),
            price='900.00',
            destination=self.destination,
            category=self.category,
            show_on_all_events=True,
        )
        hidden = Event.objects.create(
            title='All Events Hidden Ride',
            date=timezone.localdate() + timedelta(days=17),
            price='800.00',
            destination=self.destination,
            category=self.category,
        )

        response = self.client.get(reverse('experiences:all_events'))

        self.assertContains(response, shown.title)
        self.assertNotContains(response, hidden.title)

    def test_new_events_are_not_on_all_events_by_default(self):
        event = Event.objects.create(
            title='All Events Default Walk',
            date=timezone.localdate() + timedelta(days=18),
            price='200.00',
            destination=self.destination,
            category=self.category,
        )

        self.assertFalse(event.show_on_all_events)

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
            show_on_explore_your_way=True,
        )
        expensive_event = Event.objects.create(
            title='Luxury Lagoon Tour',
            date=timezone.localdate() + timedelta(days=7),
            price='1500.00',
            destination=self.destination,
            category=self.category,
            show_on_explore_your_way=True,
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


# ======================================================================
# Reviews on every kind of past booking, and destination price display
# ======================================================================

class ReviewAnyBookingTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user('mithili', 'm@example.com', 'pass12345')
        self.other = User.objects.create_user('friend', 'f@example.com', 'pass12345')
        self.yesterday = timezone.localdate() - timedelta(days=1)
        self.client.force_login(self.user)

        self.event = Event.objects.create(title='Past Hike', date=self.yesterday, price=Decimal('500'))
        self.package = Package.objects.create(title='Past Package', price=Decimal('900'))

        self.event_booking = Booking.objects.create(
            user=self.user, event=self.event, full_name='M', email='m@example.com')
        self.package_booking = Booking.objects.create(
            user=self.user, package=self.package, preferred_date=self.yesterday,
            full_name='M', email='m@example.com')
        self.place_booking = Booking.objects.create(
            user=self.user, preferred_date=self.yesterday, full_name='M', email='m@example.com',
            special_requests='Experience: Le Morne [place:le-morne]')

    def post_review(self, key, rating='5', comment='Great!'):
        return self.client.post(reverse('experiences:add_review'),
                                {'event': key, 'rating': rating, 'comment': comment})

    def test_review_event_booking(self):
        self.post_review(f'event:{self.event.pk}')
        review = Review.objects.get(user=self.user)
        self.assertEqual(review.event, self.event)
        self.assertEqual(review.subject, 'Past Hike')

    def test_plain_event_id_still_works(self):
        self.post_review(str(self.event.pk))
        self.assertEqual(Review.objects.filter(event=self.event).count(), 1)

    def test_review_package_booking(self):
        self.post_review(f'package:{self.package.pk}')
        review = Review.objects.get(user=self.user)
        self.assertIsNone(review.event)
        self.assertEqual(review.item_key, f'package:{self.package.pk}')
        self.assertEqual(review.subject, 'Past Package')

    def test_review_place_booking(self):
        self.post_review(f'item:{self.place_booking.pk}')
        review = Review.objects.get(user=self.user)
        self.assertIsNone(review.event)
        self.assertEqual(review.subject, 'Le Morne')

    def test_second_review_of_same_item_is_refused(self):
        self.post_review(f'package:{self.package.pk}')
        self.post_review(f'package:{self.package.pk}', comment='Again')
        self.assertEqual(Review.objects.filter(user=self.user).count(), 1)

    def test_cannot_review_someone_elses_booking(self):
        theirs = Booking.objects.create(
            user=self.other, preferred_date=self.yesterday, full_name='F', email='f@example.com',
            special_requests='Experience: Gris Gris [place:gris-gris]')
        self.post_review(f'item:{theirs.pk}')
        self.assertEqual(Review.objects.count(), 0)

    def test_missing_rating_or_comment_creates_nothing(self):
        self.post_review(f'event:{self.event.pk}', rating='')
        self.post_review(f'event:{self.event.pk}', comment='')
        self.assertEqual(Review.objects.count(), 0)

    def test_reviewable_lists_all_previous_cards_and_hides_reviewed(self):
        response = self.client.get(reverse('experiences:my_experiences'))
        keys = {c['key'] for c in response.context['reviewable']}
        self.assertEqual(keys, {f'event:{self.event.pk}', f'package:{self.package.pk}',
                                f'item:{self.place_booking.pk}'})

        self.post_review(f'package:{self.package.pk}')
        response = self.client.get(reverse('experiences:my_experiences'))
        keys = {c['key'] for c in response.context['reviewable']}
        self.assertNotIn(f'package:{self.package.pk}', keys)
        reviewed = {c['key']: c['reviewed'] for c in response.context['previous_experiences']}
        self.assertTrue(reviewed[f'package:{self.package.pk}'])
        self.assertFalse(reviewed[f'event:{self.event.pk}'])


class DestinationPriceDisplayTests(TestCase):
    def setUp(self):
        self.region, _ = Region.objects.get_or_create(name='South', defaults={'slug': 'south'})

    def make(self, name, price):
        return Destination.objects.create(region=self.region, name=name, price=price)

    def test_free_when_zero(self):
        self.assertEqual(self.make('Beach', Decimal('0')).price_display, 'Free')

    def test_formatted_price(self):
        self.assertEqual(self.make('Park', Decimal('1500')).price_display, 'Rs 1,500')

    def test_empty_when_no_price(self):
        self.assertEqual(self.make('Viewpoint', None).price_display, '')


# ======================================================================
# Admin dashboard: total revenue must not include cancelled bookings
# ======================================================================

class DashboardRevenueTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.staff = User.objects.create_user('admin1', 'a@example.com', 'pass12345', is_staff=True)
        self.customer = User.objects.create_user('buyer', 'b@example.com', 'pass12345')
        self.client.force_login(self.staff)
        self.event = Event.objects.create(
            title='Revenue Hike', date=timezone.localdate() + timedelta(days=3), price=Decimal('500'))

    def make_payment(self, amount, status=Payment.Status.PAID, booking_status='confirmed'):
        booking = Booking.objects.create(
            user=self.customer, event=self.event, full_name='B', email='b@example.com',
            status=booking_status)
        return Payment.objects.create(booking=booking, method='card', amount=Decimal(amount), status=status)

    def revenue(self):
        response = self.client.get(reverse('admin_dashboard:dashboard'))
        self.assertEqual(response.status_code, 200)
        return response.context['stats']['revenue']

    def test_cancelled_bookings_are_not_counted(self):
        self.make_payment('1000')
        self.make_payment('400', booking_status='cancelled')
        self.assertEqual(self.revenue(), Decimal('1000'))

    def test_unpaid_payments_are_not_counted(self):
        self.make_payment('1000')
        self.make_payment('300', status=Payment.Status.PENDING)
        self.make_payment('200', status=Payment.Status.FAILED)
        self.assertEqual(self.revenue(), Decimal('1000'))

    def test_revenue_drops_when_a_paid_booking_is_cancelled(self):
        payment = self.make_payment('700')
        self.assertEqual(self.revenue(), Decimal('700'))
        payment.booking.status = 'cancelled'
        payment.booking.save()
        self.assertEqual(self.revenue(), 0)


# ======================================================================
# Admin dashboard: bookings count must not include cancelled bookings
# ======================================================================

class DashboardBookingCountTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.staff = User.objects.create_user('admin2', 'a2@example.com', 'pass12345', is_staff=True)
        self.customer = User.objects.create_user('buyer2', 'b2@example.com', 'pass12345')
        self.client.force_login(self.staff)
        self.event = Event.objects.create(
            title='Count Hike', date=timezone.localdate() + timedelta(days=3), price=Decimal('500'))

    def make_booking(self, status):
        return Booking.objects.create(
            user=self.customer, event=self.event, full_name='B', email='b2@example.com', status=status)

    def bookings_stat(self):
        response = self.client.get(reverse('admin_dashboard:dashboard'))
        self.assertEqual(response.status_code, 200)
        return response.context['stats']['bookings']

    def test_cancelled_bookings_are_not_counted(self):
        self.make_booking('confirmed')
        self.make_booking('cancelled')
        self.assertEqual(self.bookings_stat(), 1)

    def test_pending_and_confirmed_bookings_are_counted(self):
        self.make_booking('pending')
        self.make_booking('confirmed')
        self.assertEqual(self.bookings_stat(), 2)

    def test_count_drops_when_a_booking_is_cancelled(self):
        booking = self.make_booking('confirmed')
        self.assertEqual(self.bookings_stat(), 1)
        booking.status = 'cancelled'
        booking.save()
        self.assertEqual(self.bookings_stat(), 0)


# ======================================================================
# Admin dashboard: an admin who made and paid for a booking counts as a customer
# ======================================================================

class DashboardCustomerCountTests(TestCase):
    def setUp(self):
        self.User = get_user_model()
        self.staff = self.User.objects.create_user('admin4', 'a4@example.com', 'pass12345', is_staff=True)
        self.client.force_login(self.staff)
        self.event = Event.objects.create(
            title='Customer Hike', date=timezone.localdate() + timedelta(days=3), price=Decimal('500'))

    def customers(self):
        response = self.client.get(reverse('admin_dashboard:dashboard'))
        self.assertEqual(response.status_code, 200)
        return response.context['stats']['customers']

    def book(self, user, pay_status=Payment.Status.PAID, booking_status='confirmed'):
        booking = Booking.objects.create(
            user=user, event=self.event, full_name='X', email='x@example.com', status=booking_status)
        return Payment.objects.create(booking=booking, method='card', amount=Decimal('500'), status=pay_status)

    def test_admin_with_a_paid_booking_counts_as_a_customer(self):
        before = self.customers()
        self.book(self.staff)
        self.assertEqual(self.customers(), before + 1)

    def test_admin_without_bookings_is_not_counted(self):
        before = self.customers()
        self.User.objects.create_user('admin5', 'a5@example.com', 'pass12345', is_staff=True)
        self.assertEqual(self.customers(), before)

    def test_admin_with_unpaid_booking_is_not_counted(self):
        before = self.customers()
        self.book(self.staff, pay_status=Payment.Status.PENDING)
        self.assertEqual(self.customers(), before)

    def test_admin_with_only_a_cancelled_booking_is_not_counted(self):
        before = self.customers()
        self.book(self.staff, booking_status='cancelled')
        self.assertEqual(self.customers(), before)

    def test_admin_with_several_paid_bookings_is_counted_once(self):
        before = self.customers()
        self.book(self.staff)
        self.book(self.staff)
        self.assertEqual(self.customers(), before + 1)

    def test_regular_customers_are_still_counted(self):
        before = self.customers()
        user = self.User.objects.create_user('buyer3', 'b3@example.com', 'pass12345')
        Profile.objects.get_or_create(user=user)
        self.assertEqual(self.customers(), before + 1)


# ======================================================================
# My Experiences: refund message when a paid booking is cancelled
# ======================================================================

class CancelBookingRefundTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.customer = User.objects.create_user('refunder', 'r@example.com', 'pass12345')
        self.other = User.objects.create_user('someone', 's@example.com', 'pass12345')
        self.client.force_login(self.customer)
        self.event = Event.objects.create(
            title='Refund Hike', date=timezone.localdate() + timedelta(days=3), price=Decimal('500'))

    def make_booking(self, amount=None, pay_status=Payment.Status.PAID, user=None):
        booking = Booking.objects.create(
            user=user or self.customer, event=self.event, full_name='R', email='r@example.com')
        if amount is not None:
            Payment.objects.create(booking=booking, method='card', amount=Decimal(amount), status=pay_status)
        return booking

    def cancel(self, booking):
        return self.client.post(reverse('experiences:cancel_booking', args=[booking.pk]), follow=True)

    def messages_of(self, response):
        return [str(m) for m in response.context['messages']]

    def test_paid_booking_shows_refund_message(self):
        booking = self.make_booking('550')
        response = self.cancel(booking)
        booking.refresh_from_db()
        self.assertEqual(booking.status, 'cancelled')
        self.assertTrue(any('You have been refunded Rs 550' in m for m in self.messages_of(response)))

    def test_refund_amount_is_formatted_with_thousands_separator(self):
        booking = self.make_booking('1500')
        response = self.cancel(booking)
        self.assertTrue(any('refunded Rs 1,500' in m for m in self.messages_of(response)))

    def test_booking_history_shows_refund_line_for_cancelled_paid_booking(self):
        booking = self.make_booking('550')
        self.cancel(booking)
        response = self.client.get(reverse('experiences:my_experiences'))
        self.assertContains(response, 'You have been refunded Rs 550')

    def test_unpaid_booking_gets_no_refund_message(self):
        booking = self.make_booking()
        response = self.cancel(booking)
        booking.refresh_from_db()
        self.assertEqual(booking.status, 'cancelled')
        self.assertFalse(any('refunded' in m for m in self.messages_of(response)))
        self.assertNotContains(response, 'You have been refunded')

    def test_pending_payment_gets_no_refund_message(self):
        booking = self.make_booking('550', pay_status=Payment.Status.PENDING)
        response = self.cancel(booking)
        self.assertFalse(any('refunded' in m for m in self.messages_of(response)))

    def test_cancelling_twice_does_not_refund_twice(self):
        booking = self.make_booking('550')
        self.cancel(booking)
        response = self.cancel(booking)
        self.assertFalse(any('refunded' in m for m in self.messages_of(response)))

    def test_cannot_cancel_someone_elses_booking(self):
        theirs = self.make_booking('550', user=self.other)
        response = self.client.post(reverse('experiences:cancel_booking', args=[theirs.pk]))
        theirs.refresh_from_db()
        self.assertEqual(response.status_code, 403)
        self.assertNotEqual(theirs.status, 'cancelled')


# ======================================================================
# My Experiences: past experiences cannot be cancelled
# ======================================================================

class PastBookingCancelTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.customer = User.objects.create_user('pastbuyer', 'p@example.com', 'pass12345')
        self.client.force_login(self.customer)
        self.today = timezone.localdate()
        self.yesterday = self.today - timedelta(days=1)
        self.past_event = Event.objects.create(title='Past Walk', date=self.yesterday, price=Decimal('500'))
        self.future_event = Event.objects.create(
            title='Future Walk', date=self.today + timedelta(days=4), price=Decimal('500'))
        self.today_event = Event.objects.create(title='Today Walk', date=self.today, price=Decimal('500'))

    def booking(self, **kwargs):
        defaults = dict(user=self.customer, full_name='P', email='p@example.com')
        defaults.update(kwargs)
        return Booking.objects.create(**defaults)

    def cancel_url(self, booking):
        return reverse('experiences:cancel_booking', args=[booking.pk])

    def page(self):
        return self.client.get(reverse('experiences:my_experiences'))

    def test_past_event_booking_has_no_cancel_button(self):
        booking = self.booking(event=self.past_event)
        response = self.page()
        self.assertNotContains(response, self.cancel_url(booking))
        self.assertContains(response, 'Completed')

    def test_past_package_booking_has_no_cancel_button(self):
        package = Package.objects.create(title='Old Package', price=Decimal('900'))
        booking = self.booking(package=package, preferred_date=self.yesterday)
        self.assertNotContains(self.page(), self.cancel_url(booking))

    def test_past_place_booking_has_no_cancel_button(self):
        booking = self.booking(preferred_date=self.yesterday,
                               special_requests='Experience: Le Morne [place:le-morne]')
        self.assertNotContains(self.page(), self.cancel_url(booking))

    def test_upcoming_booking_still_has_cancel_button(self):
        booking = self.booking(event=self.future_event)
        self.assertContains(self.page(), self.cancel_url(booking))

    def test_booking_today_can_still_be_cancelled(self):
        booking = self.booking(event=self.today_event)
        self.assertContains(self.page(), self.cancel_url(booking))

    def test_posting_a_cancel_for_a_past_booking_is_refused(self):
        booking = self.booking(event=self.past_event)
        Payment.objects.create(booking=booking, method='card', amount=Decimal('550'),
                               status=Payment.Status.PAID)
        response = self.client.post(self.cancel_url(booking), follow=True)
        booking.refresh_from_db()
        self.assertNotEqual(booking.status, 'cancelled')
        texts = [str(m) for m in response.context['messages']]
        self.assertTrue(any('already taken place' in t for t in texts))
        self.assertFalse(any('refunded' in t for t in texts))

    def test_upcoming_booking_can_be_cancelled(self):
        booking = self.booking(event=self.future_event)
        self.client.post(self.cancel_url(booking))
        booking.refresh_from_db()
        self.assertEqual(booking.status, 'cancelled')


# ======================================================================
# My Experiences: Booking History order (cancellable, completed, cancelled)
# ======================================================================

class BookingHistoryOrderTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.customer = User.objects.create_user('orderbuyer', 'o@example.com', 'pass12345')
        self.client.force_login(self.customer)
        today = timezone.localdate()
        self.future = Event.objects.create(title='Order Future', date=today + timedelta(days=5), price=Decimal('500'))
        self.past = Event.objects.create(title='Order Past', date=today - timedelta(days=5), price=Decimal('500'))
        self.now = timezone.now()

    def make(self, event, age_hours, status='confirmed'):
        """age_hours: how long ago it was booked (bigger = older)."""
        booking = Booking.objects.create(
            user=self.customer, event=event, full_name='O', email='o@example.com', status=status)
        Booking.objects.filter(pk=booking.pk).update(created_at=self.now - timedelta(hours=age_hours))
        return booking.pk

    def history_pks(self):
        response = self.client.get(reverse('experiences:my_experiences'))
        self.assertEqual(response.status_code, 200)
        return [b.pk for b in response.context['bookings']]

    def test_cancellable_then_completed_then_cancelled_newest_first_inside_each(self):
        a = self.make(self.future, 50)                       # cancellable, older
        b = self.make(self.past, 40)                         # completed, older
        c = self.make(self.future, 30, status='cancelled')   # cancelled, older
        d = self.make(self.future, 20)                       # cancellable, newer
        e = self.make(self.past, 10)                         # completed, newer
        f = self.make(self.past, 5, status='cancelled')      # cancelled, newer
        self.assertEqual(self.history_pks(), [d, a, e, b, f, c])

    def test_a_cancelled_booking_goes_last_even_if_it_is_the_newest(self):
        old = self.make(self.future, 30)
        newest_cancelled = self.make(self.future, 1, status='cancelled')
        self.assertEqual(self.history_pks(), [old, newest_cancelled])

    def test_booking_today_counts_as_cancellable(self):
        today_event = Event.objects.create(title='Order Today', date=timezone.localdate(), price=Decimal('500'))
        completed = self.make(self.past, 1)
        today = self.make(today_event, 30)
        self.assertEqual(self.history_pks(), [today, completed])