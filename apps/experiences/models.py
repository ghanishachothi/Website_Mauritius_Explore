from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify
from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator


class Category(models.Model):
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(unique=True, blank=True)
    icon = models.CharField(max_length=8, blank=True, help_text='Emoji shown on the card, e.g. 🎧')
    
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

    from django.core.validators import MaxValueValidator, MinValueValidator


class Review(models.Model):
    """One customer's own star rating + written comment for one event.

    Event.rating (already in the model above) stays as the admin-set overall
    average shown on cards. This table is separate: it's what a customer
    writes about their own visit, and what they can edit or delete.
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                             related_name='reviews')
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='reviews')
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text='This customer\'s own rating, 1 to 5 stars')
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(fields=['user', 'event'], name='one_review_per_user_per_event'),
        ]

    def __str__(self):
        return f'{self.user} on {self.event} ({self.rating}/5)'


class Favourite(models.Model):
    """An event a customer saved with the heart button on My Experiences."""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                             related_name='favourites')
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='favourited_by')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(fields=['user', 'event'], name='one_favourite_per_user_per_event'),
        ]

    def __str__(self):
        return f'{self.user} ♥ {self.event}'
