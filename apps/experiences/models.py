from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify
from django.conf import settings


class Category(models.Model):
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(unique=True, blank=True)
    icon = models.CharField(max_length=8, blank=True, help_text='Emoji shown on the card, e.g. 🎧')
    is_calendar_only = models.BooleanField(
        default=False,
        help_text='Only show this category on the Island Calendar page, not on All Events & Activities'
    )


    hero_title = models.CharField(max_length=100, blank=True, help_text='e.g. TASTE MAURITIUS')
    hero_subtitle = models.CharField(max_length=200, blank=True)
    hero_image = models.CharField(max_length=200, blank=True, help_text='Path in static/, e.g. images/food/hero.jpg')
    accent_color = models.CharField(max_length=7, blank=True, default='#C98B8B',
                                help_text='Hex color for buttons/active chips, e.g. #2E7D4F')
    accent_light = models.CharField(max_length=7, blank=True, default='#EFD3D3',
                                help_text='Lighter hex shade for inactive chips, e.g. #DCEEE1')



    class Meta:
        ordering = ['name']
        verbose_name_plural = 'categories'

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Event(models.Model):
    """An event / activity. Shows on All Events, Island Calendar, homepage, region pages."""
    title = models.CharField(max_length=150)
    slug = models.SlugField(unique=True, blank=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='events')
    # Link to another app's model using 'app_label.ModelName'
    destination = models.ForeignKey('destinations.Destination', on_delete=models.SET_NULL,
                                    null=True, blank=True, related_name='events')
    short_description = models.CharField(max_length=200, blank=True)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='events/', blank=True)
    date = models.DateField()
    start_time = models.TimeField(null=True, blank=True)
    end_time = models.TimeField(null=True, blank=True)
    location_name = models.CharField(max_length=150, blank=True, help_text='Meeting point shown to customers')
    price = models.DecimalField(max_digits=10, decimal_places=2, help_text='Price per person (Rs)')
    capacity = models.PositiveIntegerField(default=20)
    is_featured = models.BooleanField(default=False, help_text='Show on the homepage')
    created_at = models.DateTimeField(auto_now_add=True)
    rating = models.DecimalField(max_digits=2, decimal_places=1, default=0,
                                  help_text='Average rating out of 5, e.g. 4.7')



    show_on_calendar = models.BooleanField(
        default=True,
        help_text='Show this event on the Island Calendar page (All Events always shows everything)'
    )

    CALENDAR_SECTION_CHOICES = [
        ('', 'Auto (sort by date)'),
        ('upcoming', 'Upcoming Events'),
        ('weekend', 'This Weekend'),
    ]
    calendar_section = models.CharField(
        max_length=10, choices=CALENDAR_SECTION_CHOICES, blank=True,
        help_text='Which Island Calendar column this event appears in'
    )

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
    def date_label(self):
        return self.date.strftime('%d %b')

    @property
    def time_label(self):
        if self.start_time and self.end_time:
            return f'{self.start_time.strftime("%H:%M")}-{self.end_time.strftime("%H:%M")}'
        return ''


class Favourite(models.Model):
    """One customer saving one experience to their Explore Board favourites."""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='favourites')
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='favourited_by')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'event')
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user.username} ♥ {self.event.title}'


class ChatSession(models.Model):
    session_key = models.CharField(max_length=64, unique=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    is_live_requested = models.BooleanField(default=False)
    is_resolved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Chat #{self.pk} ({'live' if self.is_live_requested else 'bot'})"


class ChatMessage(models.Model):
    SENDER_CHOICES = [
        ('user', 'User'),
        ('bot', 'Bot'),
        ('admin', 'Admin'),
    ]
    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name='messages')
    sender = models.CharField(max_length=10, choices=SENDER_CHOICES)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"{self.sender}: {self.text[:40]}"


class FAQEntry(models.Model):
    keyword = models.CharField(max_length=50, help_text="A word that triggers this answer, e.g. 'price'")
    answer = models.TextField()

    class Meta:
        verbose_name_plural = 'FAQ entries'

    def __str__(self):
        return self.keyword

class Difficulty(models.TextChoices):
    EASY = 'easy', 'Easy'
    MODERATE = 'moderate', 'Moderate'
    HARD = 'hard', 'Hard'


class Experience(models.Model):
    """Cards on any category landing page (Nature, Food, Culture, History, Experiences).
    Which page an item shows on is decided by `category` — set entirely from admin,
    never hardcoded. `kind` is free text so each category can define its own filter chips
    just by typing them in when adding an item (e.g. Food: 'Cuisine'/'Food Quests',
    Nature: 'Hiking'/'Beaches')."""

    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='experiences')
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, blank=True)
    kind = models.CharField(max_length=50, blank=True, help_text='Free text, e.g. Cuisine, Hiking, Museum')
    location = models.CharField(max_length=100, blank=True, help_text='e.g. Pamplemousses')
    rating = models.DecimalField(max_digits=2, decimal_places=1, default=4.5)
    price = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True, help_text='Price in Rs, leave blank if free')
    duration = models.CharField(max_length=50, blank=True, help_text='e.g. 2 hours, Half day (optional)')
    difficulty = models.CharField(max_length=10, choices=Difficulty.choices, blank=True, help_text='Optional — leave blank if not relevant')
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='experiences/', blank=True, help_text='Upload the photo here')
    static_image = models.CharField(max_length=200, blank=True,
                                    help_text='Or a file in static/, e.g. images/nature/hero.jpg')
    is_active = models.BooleanField(default=True, help_text='Untick to hide the card')
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order', 'name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.name} ({self.category.name})'

    @property
    def image_url(self):
        from django.templatetags.static import static
        if self.image:
            return self.image.url

        return static(self.static_image) if self.static_image else ''