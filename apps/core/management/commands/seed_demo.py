from datetime import time, timedelta

from django.core.management.base import BaseCommand
from django.urls import reverse
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
            SitePage.objects.get_or_create(name=name, defaults={
                'url': url, 'location': loc, 'header_line1': l1, 'header_line2': l2,
                'icon': icon, 'keywords': keys, 'order': i})

        # second set of header titles: the five regions
        for i, region in enumerate(Region.objects.all()):
            SitePage.objects.get_or_create(name=f'{region.name} Mauritius', defaults={
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
                'is_featured': name in ('Mont Choisy', 'Le Morne', 'Ile aux Cerfs', 'Chamarel'),
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