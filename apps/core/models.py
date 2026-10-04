"""
core app: the homepage and everything the whole site shares
(header links, side menu, footer, app badges, social links, "When to come").
Everything here is edited in /admin/ - nothing is hardcoded in the templates.
"""
import calendar

from django.db import models


ICON_CHOICES = [
    ('ticket', 'Ticket'),
    ('user', 'Person'),
    ('heart', 'Heart'),
    ('calendar', 'Calendar'),
    ('map', 'Map'),
    ('help', 'Help / question'),
    ('compass', 'Compass'),
    ('bag', 'Bag'),
    ('home', 'Home'),
    ('lock', 'Lock'),
    ('board', 'Board'),
    ('route', 'Route'),
    ('gear', 'Gear'),
    ('book', 'Book'),
]


class SitePage(models.Model):
    """A page of the website: shown in the header, the side menu and/or the search bar."""

    class Location(models.TextChoices):
        HEADER_1 = 'header1', 'Header - first set of titles'
        HEADER_2 = 'header2', 'Header - second set (after the arrow)'
        SIDE = 'side', 'Side menu (Your trip)'
        MENU = 'menu', 'Side menu (Explore the site)'
        SEARCH = 'search', 'Search bar only'

    name = models.CharField(max_length=80, help_text='e.g. Island Calendar')
    url = models.CharField(max_length=200, help_text='Path of the page, e.g. /experiences/calendar/ (or #help for the Help pop-up)')
    location = models.CharField(max_length=10, choices=Location.choices, default=Location.HEADER_1)
    header_line1 = models.CharField(max_length=40, blank=True, help_text='First line in the header (empty = name)')
    header_line2 = models.CharField(max_length=40, blank=True, help_text='Optional second line in the header')
    icon = models.CharField(max_length=20, choices=ICON_CHOICES, default='compass', help_text='Icon in the side menu')
    keywords = models.CharField(max_length=200, blank=True, help_text='Extra words the search bar should match')
    frame_ready = models.BooleanField(default=True, help_text='Untick while the page is not built yet: it is then hidden from the search bar')
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['location', 'order', 'name']

    def save(self, *args, **kwargs):
        if not self.header_line1:
            self.header_line1 = self.name
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.name} ({self.get_location_display()})'


class FooterColumn(models.Model):
    title = models.CharField(max_length=50)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order', 'title']

    def __str__(self):
        return self.title


class FooterLink(models.Model):
    column = models.ForeignKey(FooterColumn, on_delete=models.CASCADE, related_name='links')
    label = models.CharField(max_length=60)
    url = models.CharField(max_length=200, help_text='e.g. /experiences/ or #help')
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order', 'label']

    def __str__(self):
        return self.label


class AppLink(models.Model):
    """Store badges in the footer. Leave the URL empty while the app is not published ("Coming soon")."""

    class Store(models.TextChoices):
        GOOGLE = 'google', 'Google Play'
        APPLE = 'apple', 'App Store'
        HUAWEI = 'huawei', 'AppGallery'

    store = models.CharField(max_length=10, choices=Store.choices, unique=True)
    url = models.URLField(blank=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.get_store_display()


class SocialLink(models.Model):
    class Platform(models.TextChoices):
        FACEBOOK = 'facebook', 'Facebook'
        INSTAGRAM = 'instagram', 'Instagram'
        TIKTOK = 'tiktok', 'TikTok'
        YOUTUBE = 'youtube', 'YouTube'
        X = 'x', 'X'
        WHATSAPP = 'whatsapp', 'WhatsApp'
        GMAIL = 'gmail', 'Email'

    platform = models.CharField(max_length=10, choices=Platform.choices, unique=True)
    url = models.CharField(max_length=200, help_text='Full link, e.g. https://wa.me/230... or mailto:you@example.com')
    icon = models.CharField(max_length=150, help_text='Image path inside static/, e.g. images/social/facebook.png')
    show_in_footer = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.get_platform_display()


class MonthTip(models.Model):
    """One row per month for the "When to come" planner on the homepage."""

    class Crowd(models.TextChoices):
        QUIET = 'Quiet', 'Quiet'
        MODERATE = 'Moderate', 'Moderate'
        BUSY = 'Busy', 'Busy'

    month = models.PositiveSmallIntegerField(unique=True, choices=[(i, calendar.month_name[i]) for i in range(1, 13)])
    headline = models.CharField(max_length=100, blank=True, help_text='e.g. Hot, green and festive')
    air = models.PositiveSmallIntegerField(help_text='Average air temperature (°C)')
    sea = models.PositiveSmallIntegerField(help_text='Average sea temperature (°C)')
    crowd = models.CharField(max_length=10, choices=Crowd.choices, default=Crowd.MODERATE)
    note = models.CharField(max_length=200, help_text='Weather in one sentence')
    highlight = models.CharField(max_length=200, blank=True, help_text="What's on this month")

    class Meta:
        ordering = ['month']

    def __str__(self):
        return self.name

    @property
    def name(self):
        return calendar.month_name[self.month]

    @property
    def short_name(self):
        return calendar.month_abbr[self.month]


class ContactMessage(models.Model):
    """Messages sent from the Help & Contact pop-up."""

    class Topic(models.TextChoices):
        GENERAL = 'general', 'A general question'
        TRIP = 'trip', 'Planning my trip'
        BOOKING = 'booking', 'A booking'
        ACCOUNT = 'account', 'My account'

    name = models.CharField(max_length=100)
    email = models.EmailField()
    topic = models.CharField(max_length=10, choices=Topic.choices, default=Topic.GENERAL)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.name}: {self.get_topic_display()}'


class AppWaitlist(models.Model):
    """Emails from "Tell me when it's in the store"."""
    email = models.EmailField()
    store = models.CharField(max_length=10, default='any')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = [('email', 'store')]
        verbose_name_plural = 'app waitlist'

    def __str__(self):
        return f'{self.email} ({self.store})'
