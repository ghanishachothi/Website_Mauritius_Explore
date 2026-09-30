from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify
from django.conf import settings


class Category(models.Model):
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(unique=True, blank=True)
    icon = models.CharField(max_length=8, blank=True, help_text='Emoji shown on the card, e.g. 🎧')
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


class FoodExperience(models.Model):
    """Cards on the Taste Mauritius (food) frame."""

    class Kind(models.TextChoices):
        CUISINE = 'cuisine', 'Mauritian Cuisine'
        QUEST = 'quest', 'Food Quests'

    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, blank=True)
    kind = models.CharField(max_length=10, choices=Kind.choices, default=Kind.CUISINE)
    location = models.CharField(max_length=100, help_text='e.g. Pamplemousses')
    rating = models.DecimalField(max_digits=2, decimal_places=1, default=4.5)
    price = models.DecimalField(max_digits=8, decimal_places=2, help_text='Price in Rs')
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='food/', blank=True, help_text='Upload the photo here')
    static_image = models.CharField(max_length=200, blank=True,
                                    help_text='Or a file in static/, e.g. images/food/mine-bouille.jpg')
    is_active = models.BooleanField(default=True, help_text='Untick to hide the card')
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order', 'name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    @property
    def image_url(self):
        from django.templatetags.static import static
        if self.image:
            return self.image.url
        return static(self.static_image) if self.static_image else ''
