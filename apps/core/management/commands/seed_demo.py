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

        events = [
            ('Sunset Kayak at Mont Choisy', 'Water Sports', 'Mont Choisy', 3, 1500),
            ('Le Morne Summit Hike', 'Hiking', 'Le Morne', 5, 1200),
            ('Ile aux Cerfs Catamaran Day', 'Water Sports', 'Ile aux Cerfs', 8, 3500),
            ('Chamarel Food Tour', 'Food', 'Chamarel', 12, 2000),
            ('Grand Baie Street Festival', 'Culture', 'Grand Baie', 15, 0),
        ]
        for title, cat, place, days, price in events:
            Event.objects.get_or_create(title=title, defaults={
                'category': cats[cat], 'destination': dest[place],
                'date': today + timedelta(days=days), 'start_time': time(9, 0),
                'price': price, 'capacity': 20, 'is_featured': True,
                'short_description': 'Sample event - replace me in the admin.',
            })

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
