from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify


class Category(models.Model):
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(unique=True, blank=True)
    icon = models.CharField(max_length=40, blank=True,
        help_text='Font Awesome classes, e.g. fa-solid fa-mountain-sun (leave empty for an automatic icon)')
    order = models.PositiveIntegerField(default=0, help_text='Lower numbers show first on Explore Your Way')

    ICON_FALLBACKS = {
        'nature': 'fa-solid fa-mountain-sun',
        'culture': 'fa-solid fa-masks-theater',
        'heritage-and-history': 'fa-solid fa-landmark',
        'food': 'fa-solid fa-utensils',
        'food-and-drinks': 'fa-solid fa-utensils',
        'local-experiences': 'fa-solid fa-person-hiking',
        'water-sports': 'fa-solid fa-sailboat',
        'hiking': 'fa-solid fa-person-hiking',
    }

    @property
    def icon_class(self):
        """Font Awesome icon: admin-entered 'fa-solid fa-...' text wins, else a slug fallback."""
        if self.icon.startswith('fa'):
            return self.icon
        return self.ICON_FALLBACKS.get(self.slug, 'fa-solid fa-compass')

    class Meta:
        ordering = ['order', 'name']
        verbose_name_plural = 'categories'

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Event(models.Model):
    """An event / activity. Shows on All Events, Island Calendar, homepage, region pages."""
    DIFFICULTY_CHOICES = [
        ('easy', 'Easy'),
        ('moderate', 'Moderate'),
        ('challenging', 'Challenging'),
    ]

    LANGUAGE_CHOICES = [
        ('en', 'English'),
        ('fr', 'French'),
        ('en_fr', 'English, French'),
        ('en_fr_other', 'English, French, Other on request'),
    ]

    GROUP_SIZE_CHOICES = [
        ('small', 'Small group (1-10 people)'),
        ('medium', 'Medium group (11-30 people)'),
        ('large', 'Large group (30+ people)'),
    ]

    CANCELLATION_CHOICES = [
        ('24h', 'Free cancellation 24 hours in advance'),
        ('48h', 'Free cancellation 48 hours in advance'),
        ('72h', 'Free cancellation 72 hours in advance'),
        ('none', 'No free cancellation'),
    ]

    title = models.CharField(max_length=150)
    slug = models.SlugField(unique=True, blank=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='events')
    destination = models.ForeignKey('destinations.Destination', on_delete=models.SET_NULL,
                                    null=True, blank=True, related_name='events')
    short_description = models.CharField(max_length=200, blank=True)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='events/', blank=True)
    gallery_image_1 = models.ImageField(upload_to='events/gallery/', blank=True, help_text='Gallery thumbnail 1')
    gallery_image_2 = models.ImageField(upload_to='events/gallery/', blank=True, help_text='Gallery thumbnail 2')
    gallery_image_3 = models.ImageField(upload_to='events/gallery/', blank=True, help_text='Gallery thumbnail 3')
    date = models.DateField()
    start_time = models.TimeField(null=True, blank=True)
    end_time = models.TimeField(null=True, blank=True)
    location_name = models.CharField(max_length=150, blank=True, help_text='Meeting point shown to customers')
    difficulty = models.CharField(max_length=12, choices=DIFFICULTY_CHOICES, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, help_text='Base price per person (Rs)')
    premium_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True,
                                        help_text='Premium package price per person (Rs)')
    standard_package_label = models.CharField(max_length=80, blank=True, default='Standard package')
    premium_package_label = models.CharField(max_length=80, blank=True, default='Premium package')
    capacity = models.PositiveIntegerField(default=20)
    group_size_label = models.CharField(max_length=120, blank=True,
                                        help_text='Display label e.g. 4-30 people')
    group_size_type = models.CharField(max_length=10, choices=GROUP_SIZE_CHOICES, blank=True, default='medium')
    languages_supported = models.CharField(max_length=16, choices=LANGUAGE_CHOICES, blank=True, default='en_fr_other')
    pickup_details = models.CharField(max_length=150, blank=True,
                                      help_text='Pickup text e.g. 07:30 AM, Hotel pickup available')
    cancellation_policy = models.CharField(max_length=8, choices=CANCELLATION_CHOICES, blank=True, default='24h')
    inclusions = models.TextField(blank=True,
        help_text='Newline-separated items that are included in the package, e.g. Catamaran cruise')
    itinerary_text = models.TextField(blank=True,
        help_text='Newline-separated itinerary steps. Prefix a time with | to display time columns, e.g. 08:30|Hotel pickup')
    rating = models.DecimalField(max_digits=2, decimal_places=1, default=4.5, help_text='Average star rating (0-5)')
    review_count = models.PositiveIntegerField(default=0, help_text='Number of reviews shown on the card')
    guide = models.ForeignKey('destinations.Guide', on_delete=models.SET_NULL, null=True, blank=True,
                              related_name='events', help_text='Experience host / guide')
    is_featured = models.BooleanField(default=False, help_text='Show on the homepage')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['date', 'start_time']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.title} ({self.date})'

    def get_absolute_url(self):
        return reverse('experiences:event_detail', args=[self.slug])

    @property
    def spots_left(self):
        booked = (self.bookings.exclude(status='cancelled')
                  .aggregate(total=models.Sum('number_of_people'))['total'] or 0)
        return max(self.capacity - booked, 0)

    @property
    def is_past(self):
        return self.date < timezone.localdate()

    @property
    def duration_short(self):
        """Short duration label for cards: 'Up to 2 hours', 'Half Day', 'Full Day'."""
        if self.start_time and self.end_time:
            minutes = ((self.end_time.hour * 60 + self.end_time.minute)
                       - (self.start_time.hour * 60 + self.start_time.minute))
            if minutes <= 0:
                return 'Full Day'
            if minutes <= 120:
                return 'Up to 2 hours'
            if minutes <= 240:
                return 'Half Day'
            return 'Full Day'
        return 'Full Day'

    def get_inclusions_list(self):
        if not self.inclusions:
            return []
        return [line.strip() for line in self.inclusions.splitlines() if line.strip()]

    def get_itinerary_rows(self):
        if not self.itinerary_text:
            return []
        rows = []
        for line in self.itinerary_text.splitlines():
            line = line.strip()
            if not line:
                continue
            if '|' in line:
                time_part, _, description = line.partition('|')
                rows.append((time_part.strip(), description.strip()))
            else:
                rows.append(('', line))
        return rows

    def get_languages_display_label(self):
        if self.languages_supported == 'en':
            return 'English'
        if self.languages_supported == 'fr':
            return 'French'
        if self.languages_supported == 'en_fr':
            return 'English, French'
        if self.languages_supported == 'en_fr_other':
            return 'English, French\nOther languages on request'
        return 'English, French'

    def get_cancellation_label(self):
        return self.get_cancellation_policy_display() or 'Free cancellation\n24 hours in advance'

    def get_group_size_label(self):
        if self.group_size_label:
            return self.group_size_label
        if self.group_size_type == 'small':
            return 'Up to 10 people\nSmall group experience'
        if self.group_size_type == 'large':
            return '30+ people\nLarge group experience'
        return f'{max(1, self.capacity // 4)}-{self.capacity} people\nSmall group experience'

    def get_duration_label(self):
        if self.start_time and self.end_time:
            from datetime import datetime
            start = datetime.combine(self.date, self.start_time)
            end = datetime.combine(self.date, self.end_time)
            duration = (end - start).total_seconds() / 3600
            if duration <= 0:
                duration = 8
        else:
            duration = 8
        if duration >= 7:
            return f'Full Day ({max(7, int(duration))}-{min(12, int(duration) + 2)} hours)'
        if duration >= 4:
            return f'Half Day ({int(duration)} hours)'
        return f'{duration:.1g} hours'


class Review(models.Model):
    """Customer review for an Event. Managed in /admin/, shown on the Reviews tab."""
    event = models.ForeignKey('experiences.Event', on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='experience_reviews')
    rating = models.DecimalField(max_digits=2, decimal_places=1, default=5.0,
                                 help_text='Star rating 0-5, e.g. 4.8')
    title = models.CharField(max_length=150, blank=True, help_text='Short headline, e.g. Amazing day!')
    comment = models.TextField(blank=True, help_text='What did you enjoy?')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.event.title} - {self.rating}/5 by {self.user}'


class Favourite(models.Model):
    """One customer saving one Event via 'Add To Favourites'. No hardcoding."""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='experience_favourites')
    event = models.ForeignKey('experiences.Event', on_delete=models.CASCADE, related_name='favourited_by')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = ('user', 'event')

    def __str__(self):
        return f'{self.user} ♥ {self.event.title}'


