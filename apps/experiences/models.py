from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify


class Category(models.Model):
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(unique=True, blank=True)
    icon = models.CharField(max_length=8, blank=True, help_text='Emoji shown on the card, e.g. 🎧')
    is_calendar_only = models.BooleanField(
        default=False,
        help_text='Only show this category on the Island Calendar page, not on All Events & Activities'
    )

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






class ChatSession(models.Model):
    session_key = models.CharField(max_length=64, unique=True)
    user = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, blank=True)
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