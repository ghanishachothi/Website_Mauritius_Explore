# =============================================================================
# PLACE THIS FILE AT:
#   apps/experiences/management/commands/seed_my_experiences.py
# (create the two management/ and commands/ folders, each with an empty
#  __init__.py, if they don't already exist)
#
# PLACE THE 12 PHOTOS from seed_images/ INTO:
#   apps/experiences/management/commands/seed_images/
# (same folder as this file)
#
# This is only demo data, for you to see your own page working end-to-end
# while the real booking flow is still being built by your teammates. Run:
#
#   python manage.py seed_my_experiences --username mithili
#
# (swap 'mithili' for whichever account you log in with; if you omit
# --username it uses the first superuser it finds)
# =============================================================================
import datetime
from pathlib import Path

from django.contrib.auth import get_user_model
from django.core.files import File
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from apps.bookings.models import Booking, Payment
from apps.experiences.models import Category, Event, Favourite, Review

IMAGE_DIR = Path(__file__).resolve().parent / 'seed_images'
TODAY = timezone.localdate()

# (title, image file, days from today [negative = past], price, rating)
PAST_EVENTS = [
    ('Chamarel 7 Colours', 'chamarel.jpg', -40, 850, 4.2),
    ('Casela Nature Parks', 'casela.jpg', -42, 1200, 4.8),
    ('Bus Snack', 'bus_snack.webp', -49, 150, 4.5),
    ('Aapravasi Ghat', 'aapravasi_ghat.webp', -63, 200, 4.0),
]
UPCOMING_EVENTS = [
    ('Tamarin Falls, Henrietta', 'tamarin_falls.jpg', 15, 900, 4.4),
    ('Mahebourg Waterfront', 'mahebourg_waterfront.jpg', 53, 0, 3.6),
    ('Paradise Corner, Grand Baie', 'paradise_corner.jpg', 55, 300, 5.0),
]
# Events that only exist so they can be favourited (not booked)
FAVOURITE_ONLY_EVENTS = [
    ("L'aventure du Sucre", 'aventure_du_sucre.jpg', 30, 650, 4.6),
    ('Le Morne Brabant', 'le_morne.jpg', 35, 700, 4.9),
    ('Blue Marlin Restaurant', 'blue_marlin.webp', 20, 1500, 4.3),
    ('Château de Labourdonnais', 'chateau_labourdonnais.jpg', 40, 950, 4.7),
]

REVIEW_TEXT = {
    'Chamarel 7 Colours': (3, 'The view was not as expected. Though, there was bad '
                              'weather. Activities were expensive.'),
    'Casela Nature Parks': (5, 'Amazing experience. Kids had a blast during the safari.'),
    'Bus Snack': (4, 'Great Food. Affordable Prices. Excellent Service. But, we had '
                     'to wait for 30 minutes to get a table.'),
}


class Command(BaseCommand):
    help = 'Creates demo events, a booking history, reviews and favourites for one user.'

    def add_arguments(self, parser):
        parser.add_argument('--username', default=None,
                             help='Account to attach the demo bookings/reviews/favourites to.')

    def handle(self, *args, **options):
        User = get_user_model()
        if options['username']:
            try:
                user = User.objects.get(username=options['username'])
            except User.DoesNotExist:
                raise CommandError(f"No user called '{options['username']}'.")
        else:
            user = User.objects.filter(is_superuser=True).first()
            if not user:
                raise CommandError('No superuser found. Pass --username, or run createsuperuser first.')

        category, _ = Category.objects.get_or_create(name='Experiences', defaults={'icon': '\U0001F3DD'})

        def make_event(title, filename, offset_days, price, rating):
            event, created = Event.objects.get_or_create(
                title=title,
                defaults={
                    'category': category,
                    'date': TODAY + datetime.timedelta(days=offset_days),
                    'price': price,
                    'rating': rating,
                    'location_name': 'Mauritius',
                    'short_description': title,
                },
            )
            if created or not event.image:
                image_path = IMAGE_DIR / filename
                if image_path.exists():
                    with open(image_path, 'rb') as f:
                        event.image.save(filename, File(f), save=True)
                else:
                    self.stdout.write(self.style.WARNING(f'Missing photo: {image_path}'))
            return event

        def make_booking(event, status=Booking.Status.CONFIRMED, pay_status=Payment.Status.PAID):
            booking, created = Booking.objects.get_or_create(
                user=user, event=event,
                defaults={
                    'number_of_people': 2,
                    'full_name': user.get_full_name() or user.username,
                    'email': user.email or 'demo@example.com',
                    'status': status,
                },
            )
            if created:
                Payment.objects.get_or_create(
                    booking=booking,
                    defaults={
                        'method': Payment.Method.CARD,
                        'amount': booking.total_price,
                        'status': pay_status,
                        'card_last4': '4242',
                        'paid_at': timezone.now() if pay_status == Payment.Status.PAID else None,
                    },
                )
            return booking

        for title, filename, offset, price, rating in PAST_EVENTS:
            event = make_event(title, filename, offset, price, rating)
            make_booking(event)
            if title in REVIEW_TEXT:
                stars, comment = REVIEW_TEXT[title]
                Review.objects.get_or_create(
                    user=user, event=event,
                    defaults={'rating': stars, 'comment': comment},
                )

        for title, filename, offset, price, rating in UPCOMING_EVENTS:
            event = make_event(title, filename, offset, price, rating)
            make_booking(event)

        for title, filename, offset, price, rating in FAVOURITE_ONLY_EVENTS:
            event = make_event(title, filename, offset, price, rating)
            Favourite.objects.get_or_create(user=user, event=event)

        # One cancelled booking, to show that state on the page too.
        cancelled_event = make_event('7 Cascades', 'tamarin_falls.jpg', -10, 500, 4.1)
        make_booking(cancelled_event, status=Booking.Status.CANCELLED, pay_status=Payment.Status.PAID)

        self.stdout.write(self.style.SUCCESS(f'Demo data ready for {user.username}.'))
