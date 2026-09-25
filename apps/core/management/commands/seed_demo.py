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
        for i, name in enumerate(['North', 'South', 'East', 'West', 'Central']):
            regions[name], _ = Region.objects.get_or_create(
                name=name, defaults={'order': i, 'tagline': f'Discover the {name.lower()} of Mauritius'})

        places = [
            ('Mont Choisy', 'North', -20.0156, 57.5486),
            ('Grand Baie', 'North', -20.0119, 57.5806),
            ('Gris Gris', 'South', -20.5197, 57.5306),
            ('Ile aux Cerfs', 'East', -20.2717, 57.8045),
            ('Le Morne', 'West', -20.4561, 57.3150),
            ('Chamarel', 'West', -20.4278, 57.3806),
            ('Trou aux Cerfs', 'Central', -20.3156, 57.5058),
        ]
        dest = {}
        for name, region, lat, lng in places:
            dest[name], _ = Destination.objects.get_or_create(name=name, defaults={
                'region': regions[region], 'latitude': lat, 'longitude': lng,
                'short_description': f'Sample description for {name}.',
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

        self.stdout.write(self.style.SUCCESS('Demo data added. Edit or delete it any time in /admin/.'))
