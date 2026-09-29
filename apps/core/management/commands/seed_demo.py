from datetime import time, timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.destinations.models import Destination, Guide, Package, Region
from apps.experiences.models import Category, Event


class Command(BaseCommand):
    help = 'Adds sample regions, places, guides and events so pages are not empty. Safe to run twice.'

    def handle(self, *args, **options):
        today = timezone.localdate()

        regions = {}
        east_tagline = 'Where the ocean meets authentic charm.'
        east_description = (
            'The East is a blend of natural beauty, cultural heritage and tranquil villages. '
            'From idyllic islands and waterfalls to historic temples and lush landscapes, '
            'it offers a slower pace of life and authentic Mauritian experiences.'
        )
        for i, name in enumerate(['North', 'South', 'East', 'West', 'Central']):
            regions[name], _ = Region.objects.get_or_create(
                name=name,
                defaults={
                    'order': i,
                    'tagline': east_tagline if name == 'East' else f'Discover the {name.lower()} of Mauritius',
                    'description': east_description if name == 'East' else '',
                },
            )
        if not regions['East'].tagline or regions['East'].tagline.startswith('Discover the east'):
            regions['East'].tagline = east_tagline
        if not regions['East'].description:
            regions['East'].description = east_description
        regions['East'].save(update_fields=['tagline', 'description'])

        places = [
            ('Mont Choisy', 'North', -20.0156, 57.5486, 'A long, palm-fringed beach with calm water for swimming.'),
            ('Grand Baie', 'North', -20.0119, 57.5806, 'A lively seaside village and gateway to northern boat trips.'),
            ('Gris Gris', 'South', -20.5197, 57.5306, 'A dramatic southern coastline shaped by waves and cliffs.'),
            ('Ile aux Cerfs', 'East', -20.2717, 57.8045, 'A lagoon island famous for its pristine beaches and clear water.'),
            ('Belle Mare', 'East', -20.1960, 57.7740, 'A sweep of powder-white sand beside the East Coast lagoon.'),
            ('GRSE Waterfall', 'East', -20.2870, 57.7810, 'A lush river waterfall reached by boat along the Grand River South East.'),
            ('Poste de Flacq Temple', 'East', -20.1640, 57.7290, 'A peaceful cultural landmark in the historic Poste de Flacq area.'),
            ('Bras d’Eau', 'East', -20.1220, 57.7490, 'A quiet nature reserve of forest trails, birdlife and coastal scenery.'),
            ('Trou d’Eau Douce Lagoon', 'East', -20.2350, 57.7880, 'A colourful lagoon village and popular starting point for island trips.'),
            ('Le Morne', 'West', -20.4561, 57.3150, 'A dramatic peninsula beneath the iconic Le Morne mountain.'),
            ('Chamarel', 'West', -20.4278, 57.3806, 'A green highland village known for waterfalls and volcanic landscapes.'),
            ('Trou aux Cerfs', 'Central', -20.3156, 57.5058, 'A forested volcanic crater overlooking the central plateau.'),
        ]
        dest = {}
        for name, region, lat, lng, description in places:
            dest[name], _ = Destination.objects.get_or_create(name=name, defaults={
                'region': regions[region], 'latitude': lat, 'longitude': lng,
                'short_description': description,
                'is_featured': name in ('Mont Choisy', 'Le Morne', 'Ile aux Cerfs'),
            })

        cats = {n: Category.objects.get_or_create(name=n)[0] for n in ['Water Sports', 'Hiking', 'Culture', 'Food']}

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
                'category': 'Water Sports', 'place': 'Mont Choisy',
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
                'category': 'Hiking', 'place': 'Le Morne',
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
                'category': 'Water Sports', 'place': 'Ile aux Cerfs',
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
                'category': 'Food', 'place': 'Chamarel',
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
                'category': 'Culture', 'place': 'Grand Baie',
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
        for cfg in events:
            event, created = Event.objects.get_or_create(title=cfg['title'], defaults={
                'category': cats[cfg['category']], 'destination': dest[cfg['place']],
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

        ocean_guide, _ = Guide.objects.get_or_create(
            name='Ocean Blue Adventures',
            defaults={
                'languages': 'English, French, Kreol',
                'years_experience': 8,
                'rating': 4.9,
                'bio': 'Family-run catamaran operator with 10+ years sailing the East Coast lagoon.',
            },
        )
        catamaran_event = Event.objects.filter(title='Ile aux Cerfs Catamaran Day').first()
        if catamaran_event and catamaran_event.guide_id != ocean_guide.id:
            catamaran_event.guide = ocean_guide
            catamaran_event.save(update_fields=['guide'])

        for name, langs in [('Aliyah C.', 'English, French, Kreol'), ('John W.', 'English, French')]:
            guide, _ = Guide.objects.get_or_create(name=name, defaults={'languages': langs, 'years_experience': 5})
            pkg, created = Package.objects.get_or_create(
                title=f'Island Highlights with {name}', defaults={'guide': guide, 'price': 4500, 'duration': 'Full day'})
            if created:
                pkg.destinations.set([dest['Le Morne'], dest['Chamarel']])

        east_guide, _ = Guide.objects.get_or_create(
            name='East Coast Guide',
            defaults={
                'languages': 'English, French, Kreol',
                'years_experience': 5,
                'bio': 'Discover the East Coast lagoons, villages and island trails with a local guide.',
            },
        )
        east_package, created = Package.objects.get_or_create(
            title='East Coast Lagoon Day',
            defaults={
                'guide': east_guide,
                'description': 'Explore the East Coast lagoon, visit Île aux Cerfs and discover quiet shoreline villages.',
                'price': 4200,
                'duration': 'Full day',
                'is_featured': True,
            },
        )
        if created:
            east_package.destinations.set([
                dest['Ile aux Cerfs'],
                dest['Belle Mare'],
                dest['Trou d’Eau Douce Lagoon'],
            ])

        self.stdout.write(self.style.SUCCESS('Demo data added. Edit or delete it any time in /admin/.'))
