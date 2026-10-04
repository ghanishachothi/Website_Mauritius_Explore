import os

from datetime import time, timedelta

from django.conf import settings
from django.core.files.base import File
from django.core.management.base import BaseCommand, CommandError
from django.urls import reverse
from django.utils.text import slugify
from django.utils import timezone

from apps.core.models import AppLink, FooterColumn, FooterLink, MonthTip, SitePage, SocialLink
from apps.destinations.models import Destination, Guide, Package, Region
from apps.experiences.models import Category, Event


class Command(BaseCommand):
    help = ('Adds starter content (header/footer links, months, regions, places, guides, events) '
            'so pages are not empty. Safe to run twice. Edit everything afterwards in /admin/.')

    def handle(self, *args, **options):
        self.demo_content()   # regions first: the header and footer link to them
        self.site_content()
        self.stdout.write(self.style.SUCCESS('Starter content added. Edit or delete it any time in /admin/.'))

    # ------------------------------------------------------------------ site
    def site_content(self):
        u = reverse
        pages = [
            # name, url, location, line1, line2, icon, keywords
            ('Explore the Island', u('destinations:explore_island'), 'header1', 'Explore', 'the Island', 'map', 'map regions north south east west central'),
            ('Island Calendar', u('experiences:island_calendar'), 'header1', 'Island', 'Calendar', 'calendar', 'dates festivals month'),
            ('Events & Activities', u('experiences:all_events'), 'header1', 'Events &', 'Activities', 'ticket', 'things to do activities'),
            ('Guides & Packages', u('destinations:guides_packages'), 'header1', 'Guides &', 'Packages', 'compass', 'tour guide package'),
            ('Explore Board', u('destinations:explore_board'), 'header1', 'Explore', 'Board', 'heart', 'ideas places board'),
            ('My Experiences', u('experiences:my_experiences'), 'side', '', '', 'ticket', 'bookings my trips'),
            ('My Profile', u('users:profile'), 'side', '', '', 'user', 'account profile'),
            ('Help & Contact', '#help', 'side', '', '', 'help', 'help contact question support'),
        ]
        for i, (name, url, loc, l1, l2, icon, keys) in enumerate(pages):
            SitePage.objects.get_or_create(name=name, location=loc, defaults={
                'url': url, 'location': loc, 'header_line1': l1, 'header_line2': l2,
                'icon': icon, 'keywords': keys, 'order': i})

        # second set of header titles: the five regions
        for i, region in enumerate(Region.objects.all()):
            SitePage.objects.get_or_create(name=f'{region.name} Mauritius', location='header2', defaults={
                'url': region.get_absolute_url(), 'location': 'header2',
                'header_line1': region.name, 'keywords': 'region', 'order': i})

        footer = {
            'Explore': [('Explore the Island', u('destinations:explore_island')),
                        ('Island Calendar', u('experiences:island_calendar')),
                        ('Events & Activities', u('experiences:all_events')),
                        ('Guides & Packages', u('destinations:guides_packages'))],
            'Regions': [(r.name, r.get_absolute_url()) for r in Region.objects.all()],
            'Your trip': [('My Experiences', u('experiences:my_experiences')),
                          ('Create Account', u('users:signup')),
                          ('Log in', u('users:login'))],
            'Help': [('Contact Us', '#help')],
        }
        for i, (title, links) in enumerate(footer.items()):
            column, _ = FooterColumn.objects.get_or_create(title=title, defaults={'order': i})
            for j, (label, url) in enumerate(links):
                FooterLink.objects.get_or_create(column=column, label=label, defaults={'url': url, 'order': j})

        for i, store in enumerate(['google', 'apple', 'huawei']):
            AppLink.objects.get_or_create(store=store, defaults={'order': i})   # no url = "Coming soon"

        socials = [
            # platform, url (REPLACE with the real ones in /admin/), icon path inside static/
            ('facebook', 'https://www.facebook.com/', 'images/social/facebook.png', True),
            ('instagram', 'https://www.instagram.com/', 'images/social/instagram.png', True),
            ('tiktok', 'https://www.tiktok.com/', 'images/social/tiktok.png', True),
            ('whatsapp', 'https://wa.me/', 'images/social/whatsapp.png', False),
            ('gmail', 'mailto:', 'images/social/gmail.png', False),
        ]
        for i, (platform, url, icon, footer_on) in enumerate(socials):
            SocialLink.objects.get_or_create(platform=platform, defaults={
                'url': url, 'icon': icon, 'show_in_footer': footer_on, 'order': i})

        months = [
            # month, headline, air, sea, crowd, weather, what's on
            (1, 'Hot, green and festive', 30, 27, 'Busy', 'Hot and humid with tropical showers; cyclone season.', 'New Year celebrations and Thaipoosam Cavadee.'),
            (2, 'Warm sea, lush island', 30, 28, 'Moderate', 'The hottest, wettest month; cyclones are possible.', 'Chinese Spring Festival in Port Louis.'),
            (3, 'Summer winds down', 29, 28, 'Moderate', 'Still hot, with fewer showers towards the end.', 'Maha Shivaratri pilgrimage to Grand Bassin; Independence Day (12 March).'),
            (4, 'Calm and sunny', 28, 27, 'Quiet', 'Warm days and cooler evenings; rain eases off.', 'Ougadi (Telugu New Year) and Easter.'),
            (5, 'Great for hiking', 26, 26, 'Quiet', 'Dry, sunny and pleasant - ideal for the trails.', 'Labour Day (1 May); the hiking season begins.'),
            (6, 'Cool and breezy', 24, 25, 'Quiet', 'Winter starts: cooler, windier, especially in the south.', 'Kitesurfing season at Le Morne.'),
            (7, 'Winter on the island', 24, 24, 'Moderate', 'Coolest month; sunny on the north and west coasts.', 'Humpback whales arrive off the west coast.'),
            (8, 'Whale watching', 24, 23, 'Busy', 'Cool and dry, with steady trade winds.', 'Whale and dolphin watching; European summer holidays.'),
            (9, 'Spring is back', 25, 23, 'Moderate', 'Warming up, dry and sunny.', 'Père Laval pilgrimage (9 September).'),
            (10, 'Bright and dry', 26, 24, 'Moderate', 'One of the driest months; long sunny days.', 'Diwali (festival of lights) - date varies, Oct/Nov.'),
            (11, 'Warm sea again', 28, 25, 'Busy', 'Hot days and a warm sea; perfect for the beach.', 'Diwali and Arrival of Indentured Labourers Day (2 November).'),
            (12, 'Summer holidays', 29, 26, 'Busy', 'Hot and sunny with the first summer showers.', 'Christmas, New Year festivities and flamboyant trees in bloom.'),
        ]
        for m, headline, air, sea, crowd, note, highlight in months:
            MonthTip.objects.get_or_create(month=m, defaults={
                'headline': headline, 'air': air, 'sea': sea, 'crowd': crowd,
                'note': note, 'highlight': highlight})

    # ------------------------------------------------------------------ demo places/events
    def demo_content(self):
        today = timezone.localdate()

        regions = {}
        for i, name in enumerate(['North', 'South', 'East', 'West', 'Central']):
            regions[name], _ = Region.objects.get_or_create(
                name=name,
                defaults={
                    'order': i,
                    'tagline': f'Discover the {name.lower()} of Mauritius',
                },
            )

        places = [
            ('Mont Choisy', 'North', -20.0156, 57.5486, 'A long, palm-fringed beach with calm water for swimming.'),
            ('Grand Baie', 'North', -20.0119, 57.5806, 'A lively seaside village and gateway to northern boat trips.'),
            ('Gris Gris', 'South', -20.5197, 57.5306, 'A dramatic southern coastline shaped by waves and cliffs.'),
            ('Ile aux Cerfs', 'East', -20.2717, 57.8045, 'A lagoon island famous for its pristine beaches and clear water.'),
            ('Le Morne', 'West', -20.4561, 57.3150, 'A dramatic peninsula beneath the iconic Le Morne mountain.'),
            ('Chamarel', 'West', -20.4278, 57.3806, 'A green highland village known for waterfalls and volcanic landscapes.'),
            ('Trou aux Cerfs', 'Central', -20.3156, 57.5058, 'A forested volcanic crater overlooking the central plateau.'),
        ]
        dest = {}
        for name, region, lat, lng, description in places:
            dest[name], _ = Destination.objects.get_or_create(slug=slugify(name), defaults={
                'name': name,
                'region': regions[region], 'latitude': lat, 'longitude': lng,
                'short_description': description,
                'is_featured': name in ('Mont Choisy', 'Le Morne', 'Ile aux Cerfs', 'Chamarel'),
            })

        # The Explore Your Way design uses these five categories, in this order
        cats = {}
        design_order = ['Nature', 'Culture', 'Heritage and History', 'Food and Drinks', 'Local Experiences']
        for index, name in enumerate(design_order):
            category, _ = Category.objects.get_or_create(name=name)
            if category.order != index:
                category.order = index
                category.save(update_fields=['order'])
            cats[name] = category
        # Migrate any pre-rename 'Food' category out of the way (slug collision)
        legacy_food = Category.objects.filter(name='Food').first()
        if legacy_food and not legacy_food.events.exists():
            legacy_food.delete()

        # Extra destinations used by the design events below
        blue_bay, _ = Destination.objects.get_or_create(name='Blue Bay', defaults={
            'region': regions['South'], 'latitude': -20.4392, 'longitude': 57.4792,
            'short_description': 'A marine park with some of the clearest snorkelling water on the island.',
        })
        port_louis, _ = Destination.objects.get_or_create(name='Port Louis', defaults={
            'region': regions['North'], 'latitude': -20.1609, 'longitude': 57.5012,
            'short_description': 'The capital: markets, the old harbour and UNESCO heritage sites.',
        })

        design_events = [
            {
                'title': 'Blue Bay Snorkelling Adventure',
                'category': 'Nature', 'place': None, 'destination': blue_bay,
                'days': 4, 'price': 1800, 'premium_price': 2400,
                'difficulty': 'easy',
                'start': time(9, 0), 'end': time(13, 0),
                'pickup': '08:30 AM\nHotel pickup available',
                'group': '2-12 people\nSmall group experience',
                'languages': 'en_fr',
                'description': 'Discover the Blue Bay Marine Park with a guide: shallow reefs, shoals of tropical fish and a glass-bottom boat ride over the coral gardens.',
                'short': 'Guided snorkelling over the coral gardens of Blue Bay Marine Park.',
                'inclusions': 'Snorkelling gear\nGlass-bottom boat\nMarine park guide\nHotel transfers',
                'itinerary': '08:30|Hotel pickup\n09:00|Arrive at Blue Bay public beach\n09:30|Glass-bottom boat to the reef\n10:30|Guided snorkelling session\n12:30|Back to shore',
                'rating': 4.8, 'reviews': 96,
                'images': 'blue-bay-snorkelling-adventure',
            },
            {
                'title': 'Chamarel Waterfall',
                'category': 'Nature', 'place': 'Chamarel',
                'days': 6, 'price': 2200, 'premium_price': 2900,
                'difficulty': 'moderate',
                'start': time(8, 30), 'end': time(12, 30),
                'pickup': '08:00 AM\nHotel pickup available',
                'group': '4-15 people\nGuided nature walk',
                'languages': 'en_fr_other',
                'description': 'A guided half-day walk through the forest of Chamarel to the lookout of the island\'s tallest single-drop waterfall, with the Seven Coloured Earth on the way back.',
                'short': 'Half-day guided walk to the Chamarel falls lookout.',
                'inclusions': 'Nature guide\nPark entry\nBottled water\nTransport',
                'itinerary': '08:00|Hotel pickup\n09:00|Forest trail head\n10:30|Waterfall lookout\n12:00|Seven Coloured Earth stop\n14:00|Return',
                'rating': 4.7, 'reviews': 110,
                'images': 'chamarel-waterfall',
            },
            {
                'title': 'Aapravasi Ghat Heritage Walk',
                'category': 'Heritage and History', 'place': None, 'destination': port_louis,
                'days': 9, 'price': 900, 'premium_price': None,
                'difficulty': 'easy',
                'start': time(10, 0), 'end': time(13, 0),
                'pickup': 'No pickup required\nMeet at the Aapravasi Ghat entrance',
                'group': '2-20 people\nGuided heritage walk',
                'languages': 'en_fr',
                'description': 'Walk through the UNESCO-listed Aapravasi Ghat in Port Louis and follow the story of the indentured labourers who arrived here from 1834.',
                'short': 'UNESCO heritage walk through the Aapravasi Ghat depot.',
                'inclusions': 'Heritage guide\nMuseum entry\nWalking route map',
                'itinerary': '10:00|Meet at Aapravasi Ghat\n10:30|Guided museum visit\n11:30|Old harbour walk\n13:00|End of tour',
                'rating': 4.6, 'reviews': 74,
                'images': 'aapravasi-ghat-heritage-walk',
            },
        ]

        catamaran_inclusions = (
            'Catamaran cruise\n'
            'Snorkelling equipment\n'
            'BBQ Lunch & Drinks\n'
            'Hotel transfers\n'
            'Experienced crew'
        )
        catamaran_itinerary = (
            '07:30|Hotel pickup from your resort\n'
            '09:00|Depart from Trou d\'Eau Douce harbour\n'
            '10:00|First snorkelling stop on the reef\n'
            '12:30|BBQ lunch on the catamaran\n'
            '14:00|Free time on Ile aux Cerfs beach\n'
            '16:00|Return cruise with sunset views\n'
            '17:00|Hotel drop-off'
        )
        catamaran_description = (
            'Sail across the crystal clear waters of the East Coast to the Paradise like island of Ile Aux Cerfs. '
            'Enjoy snorkelling, swimming, a delicious BBQ lunch and unforgettable moments on this Catamaran day trip.'
        )

        events = [
            {
                'title': 'Sunset Kayak at Mont Choisy',
                'category': 'Local Experiences', 'place': 'Mont Choisy', 'destination': None,
                'images': 'sunset-kayak-at-mont-choisy',
                'days': 3, 'price': 1500, 'premium_price': 2200,
                'difficulty': 'easy',
                'start': time(16, 30), 'end': time(19, 0),
                'pickup': '04:00 PM\nHotel pickup available',
                'group': '2-8 people\nSmall group experience',
                'languages': 'en_fr',
                'description': 'Paddle along the lagoon of Mont Choisy as the sun sets over the northern coast.',
                'short': 'Sunset kayak tour along Mont Choisy beach.',
                'inclusions': 'Kayak and paddle\nLife jacket\nGuide\nBeach refreshments',
                'itinerary': '16:30|Meet at Mont Choisy beach\n17:00|Paddle session starts\n18:30|Sunset stop\n19:00|Back to shore',
                'rating': 4.7, 'reviews': 68,
            },
            {
                'title': 'Le Morne Summit Hike',
                'category': 'Nature', 'place': 'Le Morne', 'destination': None,
                'images': 'le-morne-summit-hike',
                'days': 5, 'price': 1200, 'premium_price': 1800,
                'difficulty': 'challenging',
                'start': time(6, 0), 'end': time(12, 0),
                'pickup': '05:30 AM\nHotel pickup available',
                'group': '4-12 people\nGuided group hike',
                'languages': 'en_fr_other',
                'description': 'An early start hike to the top of Le Morne Brabant, a UNESCO site with panoramic views.',
                'short': 'UNESCO heritage sunrise hike to Le Morne summit.',
                'inclusions': 'Hiking guide\nLight breakfast\nBottled water\nTransport',
                'itinerary': '05:30|Hotel pickup\n06:00|Trail head briefing\n08:30|Summit sunrise\n12:00|Return to base',
                'rating': 4.9, 'reviews': 156,
            },
            {
                'title': 'Ile aux Cerfs Catamaran Day',
                'category': 'Nature', 'place': 'Ile aux Cerfs', 'destination': None,
                'images': 'ile-aux-cerfs-catamaran-day',
                'days': 8, 'price': 2500, 'premium_price': 3500,
                'difficulty': 'moderate',
                'start': time(8, 0), 'end': time(17, 0),
                'pickup': '07:30 AM\nHotel Pickup Available',
                'group': '4-30 people\nSmall group experience',
                'languages': 'en_fr_other',
                'description': catamaran_description,
                'short': 'Full day catamaran cruise to Ile aux Cerfs with BBQ lunch.',
                'inclusions': catamaran_inclusions,
                'itinerary': catamaran_itinerary,
                'rating': 4.8, 'reviews': 124,
            },
            {
                'title': 'Chamarel Food Tour',
                'category': 'Food and Drinks', 'place': 'Chamarel', 'destination': None,
                'images': 'chamarel-food-tour',
                'days': 12, 'price': 2000, 'premium_price': 2800,
                'difficulty': 'easy',
                'start': time(10, 0), 'end': time(16, 0),
                'pickup': '09:30 AM\nHotel pickup available',
                'group': '2-10 people\nIntimate food walk',
                'languages': 'en_fr',
                'description': 'A culinary walk through Chamarel village, tasting street food and local rum distillery.',
                'short': 'Curated Chamarel village food tasting tour.',
                'inclusions': 'Local guide\n5 food tastings\nRum tasting\nTransport',
                'itinerary': '10:00|Chamarel village meetup\n11:00|Street food stop\n13:00|Rhum distillery tour\n15:00|Waterfall stop\n16:00|Return',
                'rating': 4.6, 'reviews': 92,
            },
            {
                'title': 'Grand Baie Street Festival',
                'category': 'Culture', 'place': 'Grand Baie', 'destination': None,
                'images': 'grand-baie-street-festival',
                'days': 15, 'price': 0, 'premium_price': None,
                'difficulty': 'easy',
                'start': time(18, 0), 'end': time(23, 0),
                'pickup': 'Public event\nNo pickup required',
                'group': 'Open to all\nGeneral admission',
                'languages': 'en_fr_other',
                'description': 'A monthly street festival in Grand Baie featuring live music, dance and local stalls.',
                'short': 'Free cultural street festival in Grand Baie.',
                'inclusions': 'Live shows\nDance performances\nStreet stalls (pay as you go)',
                'itinerary': '18:00|Festival opens\n19:30|Live music stage\n21:00|Dance show\n23:00|Closing',
                'rating': 4.4, 'reviews': 48,
            },
        ]
        def attach_images(event, folder):
            """Copy packaged demo photos into the event's gallery (admin uploads can replace them)."""
            source = os.path.join(settings.BASE_DIR, 'static', 'images', 'events', folder)
            if not os.path.isdir(source):
                return
            fields = ['image', 'gallery_image_1', 'gallery_image_2', 'gallery_image_3']
            if folder == 'ile-aux-cerfs-catamaran-day':
                # Replace the earlier demo gallery's harbor and ship-diagram images only.
                photos = [
                    (
                        'image',
                        os.path.join(source, 'ile-aux-cerfs-catamaran-at-sea.jpg'),
                        'ile-aux-cerfs-catamaran-at-sea.jpg',
                        (
                            'ile-aux-cerfs-catamaran-day-1',
                            'ile-aux-cerfs-catamaran-primary',
                        ),
                    ),
                    (
                        'gallery_image_1',
                        os.path.join(settings.BASE_DIR, 'static', 'images', 'east', 'ile-aux-cerfs.jpg'),
                        'ile-aux-cerfs-catamaran-island.jpg',
                        ('ile-aux-cerfs-catamaran-day-2',),
                    ),
                    (
                        'gallery_image_2',
                        os.path.join(settings.BASE_DIR, 'static', 'images', 'ile-aux-cerfs.jpg'),
                        'ile-aux-cerfs-catamaran-lagoon.jpg',
                        ('ile-aux-cerfs-catamaran-day-3',),
                    ),
                ]
                missing_photos = [path for _, path, _, _ in photos if not os.path.isfile(path)]
                if missing_photos:
                    raise CommandError(f'Missing Catamaran demo photos: {", ".join(missing_photos)}')
            else:
                files = sorted(
                    f for f in os.listdir(source)
                    if f.lower().endswith(('.jpg', '.jpeg', '.png'))
                )
                photos = [
                    (field, os.path.join(source, filename), filename, ())
                    for field, filename in zip(fields, files)
                ]

            changed = False
            for field, photo_path, filename, legacy_prefixes in photos:
                current_photo = getattr(event, field)
                is_old_catamaran_demo_photo = (
                    any(
                        os.path.basename(current_photo.name).startswith(prefix)
                        for prefix in legacy_prefixes
                    )
                )
                if current_photo and not is_old_catamaran_demo_photo:
                    continue  # an admin-uploaded photo is already there - never overwrite
                with open(photo_path, 'rb') as fh:
                    getattr(event, field).save(filename, File(fh), save=False)
                changed = True
            if changed:
                event.save()

        for cfg in design_events + events:
            place = cfg.get('destination') or dest.get(cfg['place'])
            event, created = Event.objects.get_or_create(slug=slugify(cfg['title']), defaults={
                'title': cfg['title'],
                'category': cats[cfg['category']], 'destination': place,
                'date': today + timedelta(days=cfg['days']), 'start_time': cfg['start'],
                'end_time': cfg['end'],
                'price': cfg['price'], 'premium_price': cfg['premium_price'],
                'capacity': 30, 'is_featured': True,
                'difficulty': cfg['difficulty'],
                'description': cfg['description'],
                'short_description': cfg['short'],
                'pickup_details': cfg['pickup'],
                'group_size_label': cfg['group'],
                'languages_supported': cfg['languages'],
                'inclusions': cfg['inclusions'],
                'itinerary_text': cfg['itinerary'],
                'rating': cfg['rating'],
                'review_count': cfg['reviews'],
            })
            if not created:
                changed = False
                for field, value in [
                    ('category', cats[cfg['category']]), ('destination', place),
                    ('premium_price', cfg['premium_price']), ('difficulty', cfg['difficulty']),
                    ('pickup_details', cfg['pickup']), ('group_size_label', cfg['group']),
                    ('languages_supported', cfg['languages']), ('inclusions', cfg['inclusions']),
                    ('itinerary_text', cfg['itinerary']), ('rating', cfg['rating']),
                    ('review_count', cfg['reviews']), ('description', cfg['description']),
                    ('short_description', cfg['short']), ('start_time', cfg['start']),
                    ('end_time', cfg['end']), ('price', cfg['price']), ('capacity', 30),
                ]:
                    if getattr(event, field) != value:
                        setattr(event, field, value)
                        changed = True
                if changed:
                    event.save()
            attach_images(event, cfg['images'])

        # Retire old categories if nothing uses them any more
        for legacy in ('Water Sports', 'Hiking', 'Food'):
            leftover = Category.objects.filter(name=legacy).first()
            if leftover and not leftover.events.exists():
                leftover.delete()

        # Keep titles in step with the Figma frames
        renames = {
            'Ile aux Cerfs Catamaran Day': 'Catamaran Cruise to Ile Aux Cerfs',
        }
        for old, new in renames.items():
            Event.objects.filter(title=old).update(title=new)

        ocean_guide, _ = Guide.objects.get_or_create(
            name='Ocean Blue Adventures',
            defaults={
                'languages': 'English, French, Kreol',
                'years_experience': 8,
                'rating': 4.9,
                'bio': 'Family-run catamaran operator with 10+ years sailing the East Coast lagoon.',
            },
        )
        catamaran_event = Event.objects.filter(title='Catamaran Cruise to Ile Aux Cerfs').first()
        if catamaran_event and catamaran_event.guide_id != ocean_guide.id:
            catamaran_event.guide = ocean_guide
            catamaran_event.save(update_fields=['guide'])

        for name, langs in [('Aliyah C.', 'English, French, Kreol'), ('John W.', 'English, French')]:
            guide, _ = Guide.objects.get_or_create(name=name, defaults={'languages': langs, 'years_experience': 5})
            pkg, created = Package.objects.get_or_create(
                title=f'Island Highlights with {name}', defaults={'guide': guide, 'price': 4500, 'duration': 'Full day'})
            if created:
                pkg.destinations.set([dest['Le Morne'], dest['Chamarel']])