import calendar
from django.db import models
from django.conf import settings
from django.templatetags.static import static
from django.urls import reverse
from django.utils.text import slugify
from django.utils import timezone
from django.core.validators import MaxValueValidator, MinValueValidator
import secrets


# ======================================================================
# from the old "core" app
# ======================================================================

"""
core app: the homepage and everything the whole site shares
(header links, side menu, footer, app badges, social links, "When to come").
Everything here is edited in /admin/ - nothing is hardcoded in the templates.
"""



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


# ======================================================================
# from the old "users" app
# ======================================================================

class Profile(models.Model):

    class AuthProvider(models.TextChoices):
        EMAIL = 'email', 'Email'
        GOOGLE = 'google', 'Google'
        FACEBOOK = 'facebook', 'Facebook'

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='profile'
    )
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    bio = models.TextField(blank=True, default='')
    gender = models.CharField(max_length=20, blank=True, default='')
    language = models.CharField(max_length=100, blank=True, default='')
    phone_number = models.CharField(max_length=20, blank=True, default='')
    nationality = models.CharField(max_length=100, blank=True, default='')
    deletion_requested = models.BooleanField(default=False)
    #can_book = models.BooleanField(default=True)

    provider = models.CharField(
        max_length=10,
        choices=AuthProvider.choices,
        default=AuthProvider.EMAIL
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.user.username} ({"Admin" if self.user.is_staff else "Customer"})'

    @property
    def phone(self):
        """Alias for phone_number to prevent breakage in external views accessing .phone."""
        return self.phone_number


# ======================================================================
# from the old "destinations" app
# ======================================================================

"""
destinations app: Explore the Island + everything that hangs off it.

    Region        -> North / South / East / West / Central
                     (Explore the Island cards + each friend's region frame)
    Destination   -> every place (region lists, search, Google map, Top Destinations)
    Guide, Package-> Guides & Packages
    HeroTile      -> the 4 captions on the Explore the Island hero photo
    WayToExplore  -> the 5 "Ways to explore" cards
    Suggestion    -> ideas sent with "Suggest an idea"

Teammates: USE these fields in your templates; ask the owner before adding new ones.
"""


class Region(models.Model):
    region_places = models.ManyToManyField('explore.Destination', blank=True, related_name='shown_on_regions', help_text='Choose the places that appear on this Region page. The events at these places appear on it too.')
    """North, South, East, West, Central."""

    class Scrim(models.TextChoices):
        LIGHT = 'light', 'White fade'
        DARK = 'dark', 'Soft white fade'
        WIDE = 'wide', 'Sand fade (wide card)'

    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(unique=True, blank=True)
    tagline = models.CharField(max_length=150, blank=True, help_text='Short text on the region card')
    description = models.TextField(blank=True)

    about_text = models.TextField(blank=True, help_text='"About the [Region]" paragraph')
    about_image = models.ImageField(upload_to='regions/about/', blank=True)
    travel_tip_image = models.ImageField(upload_to='regions/traveltip/', blank=True)
    travel_tip = models.TextField(blank=True, help_text='Travel Tip box text')
    theme_color = models.CharField(max_length=7, default='#2b1d10', help_text='Main background colour')
    card_color = models.CharField(max_length=7, default='#24170c', help_text='Card / panel colour')
    accent_color = models.CharField(max_length=7, default='#f0a63a', help_text='Titles, icons, Travel Tip card')
    image = models.ImageField(upload_to='regions/', blank=True, help_text='Upload a photo (optional)')
    static_image = models.CharField(max_length=200, blank=True,
                                    help_text='Used when no photo is uploaded, e.g. images/explore/regions/north.jpg')
    list_title = models.CharField(max_length=60, blank=True, help_text='Title in the "View all region" list')
    scrim = models.CharField(max_length=10, choices=Scrim.choices, default=Scrim.LIGHT,
                             help_text='How the photo fades into the text on the card')
    is_wide = models.BooleanField(default=False, help_text='Card takes the full width (Central)')
    hero_gradient = models.BooleanField(default=True, help_text='Dark fade at the bottom of the top photo. Untick for light photos')
    hero_dark_text = models.BooleanField(default=False, help_text='Use dark text on the top photo. Tick for light photos')
    keywords = models.CharField(max_length=255, blank=True, help_text='Extra words the search bar should match')

    order = models.PositiveIntegerField(default=0, help_text='Lower numbers show first')

    class Meta:
        ordering = ['order', 'name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('destinations:region_detail', args=[self.slug])

    @property
    def image_url(self):
        if self.image:
            return self.image.url
        return static(self.static_image) if self.static_image else ''


class Destination(models.Model):
    """A place: Mont Choisy, Le Morne, Ile aux Cerfs..."""
    region = models.ForeignKey(Region, on_delete=models.PROTECT, related_name='destinations')
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, blank=True)
    short_description = models.CharField(max_length=200, blank=True)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='destinations/', blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    is_featured = models.BooleanField(default=False, help_text='Show on the homepage')
    area = models.CharField(max_length=100, blank=True, help_text='Text under the name on the card, e.g. Blue Bay')
    order = models.PositiveIntegerField(default=0, help_text='Top Destinations order (lower = first)')
    note = models.CharField(max_length=80, blank=True, help_text='Small grey text in lists, e.g. fishing village')
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True,
                                help_text='Price in Rs. Enter 0 for free, leave empty to hide the price.')
    keywords = models.CharField(max_length=255, blank=True, help_text='Extra words the search bar should match')

    class Meta:
        ordering = ['order', 'name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('destinations:destination_detail', args=[self.slug])

    @property
    def region_url(self):
        """Opens the region frame on this place, e.g. /destinations/region/central/?place=minissy-waterfall"""
        return f'{self.region.get_absolute_url()}?place={self.slug}'
    
    @property
    def price_display(self):
        """'Rs 1,500', 'Free', or '' when no price is set."""
        if self.price is None:
            return ''
        if self.price == 0:
            return 'Free'
        return f'Rs {self.price:,.0f}'


class Guide(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, blank=True)
    photo = models.ImageField(upload_to='guides/', blank=True)
    role = models.CharField(max_length=100, blank=True,
                             help_text="e.g. Marine Biology Expert. Shown under their name.")
    bio = models.TextField(blank=True)
    about = models.TextField(blank=True, help_text='Longer text for the About box on the guide page. If empty, the Bio is shown there.')
    languages = models.CharField(max_length=150, blank=True, help_text='e.g. English, French, Kreol')
    years_experience = models.PositiveIntegerField(default=0)
    rating = models.DecimalField(max_digits=2, decimal_places=1, default=5.0)
    review_count = models.PositiveIntegerField(default=0)
    specialities = models.CharField(max_length=200, blank=True,
                                     help_text="Comma-separated tags, e.g. Snorkeling, Cruises, Marine life")
    location = models.CharField(max_length=100, blank=True,
                                 help_text="e.g. Blue Bay, Mauritius. Shown on the Guide Profile page.")
    travelers_count = models.PositiveIntegerField(default=0,
                                 help_text="Shown as e.g. '130+ Happy Travelers' on the Guide Profile page.")
    certified = models.BooleanField(default=True,
                                 help_text="Shows the 'Certified Local Expert' badge on the Guide Profile page.")
    why_travel_with_me = models.TextField(blank=True,
                                 help_text="One reason per line. Shown as a bullet list on the Guide Profile page.")
    detailed_specialities = models.TextField(blank=True,
                                help_text="One speciality per line. Shown in the bigger 'My Specialities' "
                                        "grid on the Guide Profile page. Can differ from the short "
                                        "'Specialities' tags used elsewhere on the site.")
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('destinations:guide_detail', args=[self.slug])

    def is_available_on(self, day):
        """True when the guide is active and not marked unavailable on this date."""
        if not self.is_active:
            return False
        return not self.unavailable_periods.filter(start_date__lte=day, end_date__gte=day).exists()

    @property
    def speciality_list(self):
        return [item.strip() for item in self.specialities.split(",") if item.strip()]

    @property
    def language_list(self):
        return [item.strip() for item in self.languages.split(",") if item.strip()]

    @property
    def why_list(self):
        return [line.strip() for line in self.why_travel_with_me.splitlines() if line.strip()]

    @property
    def detailed_speciality_list(self):
        return [line.strip() for line in self.detailed_specialities.splitlines() if line.strip()]


class GuideUnavailability(models.Model):
    """A period when a guide cannot take bookings (holiday, illness, other tour). Managed by admin."""
    guide = models.ForeignKey(Guide, on_delete=models.CASCADE, related_name='unavailable_periods')
    start_date = models.DateField()
    end_date = models.DateField(help_text='Last day the guide is unavailable (same as start for one day)')
    reason = models.CharField(max_length=150, blank=True, help_text='Optional, e.g. Annual leave')

    class Meta:
        ordering = ['start_date']
        verbose_name = 'guide unavailable period'
        verbose_name_plural = 'guide availability (unavailable periods)'

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.start_date and self.end_date and self.end_date < self.start_date:
            raise ValidationError({'end_date': 'The end date cannot be before the start date.'})

    def __str__(self):
        return f'{self.guide.name}: {self.start_date} to {self.end_date}'


class Package(models.Model):
    title = models.CharField(max_length=150)
    slug = models.SlugField(unique=True, blank=True)
    guide = models.ForeignKey(Guide, on_delete=models.SET_NULL, null=True, blank=True, related_name='packages')
    eligible_guides = models.ManyToManyField(Guide, blank=True, related_name='eligible_packages',
                                help_text="Guides a visitor can choose from when reserving this package. "
                                        "Leave empty to only offer the package's primary guide above.")
    destinations = models.ManyToManyField(Destination, blank=True, related_name='packages')
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='packages/', blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    duration = models.CharField(max_length=50, blank=True, help_text='e.g. Half day, 3 days')
    rating = models.DecimalField(max_digits=2, decimal_places=1, default=5.0)
    review_count = models.PositiveIntegerField(default=0)
    location = models.CharField(max_length=100, blank=True)
    difficulty = models.CharField(max_length=50, blank=True, help_text="e.g. Easy, Easy - Moderate")
    max_people = models.PositiveIntegerField(default=10)
    includes = models.TextField(blank=True, help_text="One inclusion per line.")
    tags = models.CharField(max_length=200, blank=True,
                             help_text="Comma-separated, used by the search filter, e.g. snorkeling, marine-life")
    languages = models.CharField(max_length=150, blank=True,
                                  help_text="Comma-separated. Leave blank to use the guide's languages.")
    is_featured = models.BooleanField(default=False)
    booking_open = models.TimeField(null=True, blank=True, help_text='Earliest time customers can book, e.g. 09:00. Leave blank for 06:00.')
    booking_close = models.TimeField(null=True, blank=True, help_text='Latest time customers can book, e.g. 17:00. Leave blank for 22:00.')

    class Meta:
        ordering = ['title']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title




    @property
    def guide_choices(self):
        chosen = list(self.eligible_guides.filter(is_active=True))
        if self.guide and self.guide not in chosen:
            chosen.insert(0, self.guide)
        return chosen or ([self.guide] if self.guide else [])

    @property
    def includes_list(self):
        return [line.strip() for line in self.includes.splitlines() if line.strip()]

    @property
    def display_languages(self):
        return self.languages or (self.guide.languages if self.guide else "")

    @property
    def search_text(self):
        return " ".join([self.title, self.description, self.includes]).lower()


class GuideReview(models.Model):
    """A traveller review of a Guide. Admin-editable — nothing hardcoded."""
    guide = models.ForeignKey(Guide, on_delete=models.CASCADE, related_name='reviews')
    traveller_name = models.CharField(max_length=100)
    avatar = models.ImageField(upload_to='reviews/', blank=True)
    rating = models.DecimalField(max_digits=2, decimal_places=1, default=5.0)
    date = models.DateField()
    text = models.TextField()

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return f"{self.traveller_name} on {self.guide.name}"


# ---------------------------------------------------------------- Explore the Island page
class HeroTile(models.Model):
    """The 4 captions on the Explore the Island hero photo."""

    class Color(models.TextChoices):
        HERITAGE = 'heritage', 'Teal'
        LOCAL = 'local', 'Orange'
        ADVENTURE = 'adventure', 'Green'
        BEAUTY = 'beauty', 'Blue'

    tag = models.CharField(max_length=30, help_text='e.g. HERITAGE')
    text = models.CharField(max_length=80, help_text='e.g. Timeless traditions and rich culture')
    color = models.CharField(max_length=10, choices=Color.choices)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order', 'id']

    def __str__(self):
        return self.tag


class WayToExplore(models.Model):
    """The "Ways to explore" cards."""
    title = models.CharField(max_length=60)
    text = models.CharField(max_length=120)
    url = models.CharField(max_length=200, help_text='Page it opens, e.g. /experiences/?category=food')
    image = models.ImageField(upload_to='ways/', blank=True, help_text='Upload a photo (optional)')
    static_image = models.CharField(max_length=200, blank=True,
                                    help_text='Used when no photo is uploaded, e.g. images/explore/ways/hike-and-explore.jpg')
    keywords = models.CharField(max_length=255, blank=True, help_text='Words that find this card in search')
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order', 'id']
        verbose_name = 'way to explore'
        verbose_name_plural = 'ways to explore'

    def __str__(self):
        return self.title

    @property
    def image_url(self):
        if self.image:
            return self.image.url
        return static(self.static_image) if self.static_image else ''


class Suggestion(models.Model):
    """Ideas sent with the "Suggest an idea" button."""
    name = models.CharField(max_length=80, blank=True)
    email = models.EmailField(blank=True)
    region = models.ForeignKey(Region, on_delete=models.SET_NULL, null=True, blank=True)
    idea = models.TextField(max_length=2000)
    is_reviewed = models.BooleanField(default=False, help_text='Tick when the team has looked at it')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.idea[:50]


class RegionHighlight(models.Model):
    """One icon+label item in the region's 'Highlights' list (e.g. Pristine Beaches)."""
    region = models.ForeignKey(Region, on_delete=models.CASCADE, related_name='highlights')
    icon = models.CharField(max_length=50, help_text='Font Awesome class, e.g. fa-solid fa-umbrella-beach')
    label = models.CharField(max_length=100)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order', 'label']

    def __str__(self):
        return f'{self.region.name} - {self.label}'


# ======================================================================
# from the old "experiences" app
# ======================================================================

class Category(models.Model):
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(unique=True, blank=True)
    icon = models.CharField(max_length=40, blank=True,
        help_text='Emoji shown on the card (e.g. 🎧) or Font Awesome classes (e.g. fa-solid fa-mountain-sun)')
    is_calendar_only = models.BooleanField(
        default=False,
        help_text='Only show this category on the Island Calendar page, not on All Events & Activities'
    )
    order = models.PositiveIntegerField(default=0, help_text='Lower numbers show first on Explore Your Way')
    show_on_board = models.BooleanField(default=True, help_text='Untick to hide this category from the Explore Board chips. It stays everywhere else.')


    hero_title = models.CharField(max_length=100, blank=True, help_text='e.g. TASTE MAURITIUS')
    hero_subtitle = models.CharField(max_length=200, blank=True)
    hero_image = models.CharField(max_length=200, blank=True, help_text='Path in static/, e.g. images/food/hero.jpg')
    accent_color = models.CharField(max_length=7, blank=True, default='#C98B8B',
                                help_text='Hex color for buttons/active chips, e.g. #2E7D4F')
    accent_light = models.CharField(max_length=7, blank=True, default='#EFD3D3',
                                help_text='Lighter hex shade for inactive chips, e.g. #DCEEE1')


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
    destination = models.ForeignKey('explore.Destination', on_delete=models.SET_NULL,
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
    guide = models.ForeignKey('explore.Guide', on_delete=models.SET_NULL, null=True, blank=True,
                              related_name='events', help_text='Experience host / guide')
    is_featured = models.BooleanField(default=False, help_text='Show on the homepage')
    created_at = models.DateTimeField(auto_now_add=True)
    rating = models.DecimalField(max_digits=2, decimal_places=1, default=0,
                                  help_text='Average rating out of 5, e.g. 4.7')



    show_on_calendar = models.BooleanField(
        default=True,
        help_text='Show this event on the Island Calendar page (All Events always shows everything)'
    )
    show_on_all_events = models.BooleanField(
        default=False,
        help_text='Show this event on the All Events & Activities page'
    )
    show_on_explore_your_way = models.BooleanField(
        default=False,
        help_text='Show this event on the Explore Your Way page'
    )
    show_on_explore_board = models.BooleanField(
        default=False,
        help_text='Show this event in Recommended for you on the Explore Board page'
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
        booked = (self.bookings.exclude(status__in=['cancelled', 'rejected'])
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
        if self.start_time and self.start_time.hour >= 17:
            return 'Night'
        if duration >= 7:
            return f'Full Day ({max(7, int(duration))}-{min(12, int(duration) + 2)} hours)'
        if duration >= 4:
            return f'Half Day ({int(duration)} hours)'
        return f'{duration:.1g} hours'

    @property
    def date_label(self):
        return self.date.strftime('%d %b')

    @property
    def time_label(self):
        if self.start_time and self.end_time:
            return f'{self.start_time.strftime("%H:%M")}-{self.end_time.strftime("%H:%M")}'
        return ''

class Review(models.Model):
    """One customer's review of one experience they've been on. Used by My Experiences
    (submit/edit/delete) - a user can only review a given event once."""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reviews')
    event = models.ForeignKey(Event, null=True, blank=True, on_delete=models.CASCADE, related_name='reviews')
    item_key = models.CharField(max_length=60, blank=True, help_text='For package/place/experience bookings, e.g. package:3')
    item_title = models.CharField(max_length=150, blank=True)
    rating = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    title = models.CharField(max_length=150, blank=True, help_text='Short headline, e.g. Amazing day!')
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'event')
        ordering = ['-created_at']

    @property
    def subject(self):
        return self.event.title if self.event_id else self.item_title

    def __str__(self):
        return f'{self.user.username} rated {self.subject} {self.rating}/5'


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
    long_description = models.TextField(blank=True, help_text='Longer text for the insight page. Leave empty to use the short description.')
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True, help_text='For the map on the insight page, e.g. -20.289300')
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True, help_text='For the map on the insight page, e.g. 57.401500')
    image = models.ImageField(upload_to='experiences/', blank=True, help_text='Upload the photo here')
    static_image = models.CharField(max_length=200, blank=True,
                                    help_text='Or a file in static/, e.g. images/nature/hero.jpg')
    is_active = models.BooleanField(default=True, help_text='Untick to hide the card')
    order = models.PositiveIntegerField(default=0)
    booking_open = models.TimeField(null=True, blank=True, help_text='Earliest time customers can book, e.g. 09:00. Leave blank for 06:00.')
    booking_close = models.TimeField(null=True, blank=True, help_text='Latest time customers can book, e.g. 17:00. Leave blank for 22:00.')

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


# ======================================================================
# from the old "bookings" app
# ======================================================================

def generate_reference():
    return 'ME-' + secrets.token_hex(3).upper()


class Booking(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending payment'
        CONFIRMED = 'confirmed', 'Confirmed'
        CANCELLED = 'cancelled', 'Cancelled'
        REJECTED = 'rejected', 'Rejected'

    reference = models.CharField(max_length=12, unique=True, default=generate_reference, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='bookings')

    # A booking is for EITHER an Event OR a Package (never both, never neither).
    event = models.ForeignKey('explore.Event', on_delete=models.PROTECT, related_name='bookings',
                               null=True, blank=True)
    package = models.ForeignKey('explore.Package', on_delete=models.PROTECT, related_name='bookings',
                                 null=True, blank=True)
    guide = models.ForeignKey('explore.Guide', on_delete=models.SET_NULL, related_name='chosen_bookings',
                               null=True, blank=True,
                               help_text="The guide the visitor chose. Only used for Package bookings.")

    # Only used for Package bookings (Events already have their own fixed date).
    preferred_date = models.DateField(null=True, blank=True)
    alternative_date = models.DateField(null=True, blank=True)

    number_of_people = models.PositiveIntegerField(default=1)
    full_name = models.CharField(max_length=150)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True)
    special_requests = models.TextField(blank=True)
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    booking_fee = models.DecimalField(max_digits=10, decimal_places=2, default=50,
    help_text='Flat fee added once per booking (Rs)')
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if self.package_id:
            unit_price = self.package.price
        elif self.event_id:
            unit_price = self.event.price
        else:
            unit_price = getattr(self, '_unit_price', None)
        if unit_price is not None:
            self.total_price = unit_price * self.number_of_people + self.booking_fee
        super().save(*args, **kwargs)

    def __str__(self):
        item = self.display_title
        return f'{self.reference} - {item} ({self.user.username})'

    # --- Experience / place bookings: no Event or Package, the name is kept in special_requests ---
    @property
    def _item_ref(self):
        import re
        mt = re.search(r'(?m)^Experience: (.+?) \[(experience|place):([\w-]+)\]', self.special_requests or '')
        return mt.groups() if mt else None

    @property
    def display_title(self):
        _o = self.__dict__.get('_display_title')
        if _o:
            return _o
        if self.event_id:
            return self.event.title
        if self.package_id:
            return self.package.title
        ref = self._item_ref
        if ref:
            _pl = self.chosen_place
            return ref[0] + ((' - ' + _pl) if _pl else '')
        return f'booking {self.reference}'

    @property
    def display_image_url(self):
        from django.templatetags.static import static
        if self.event_id:
            return self.event.image.url if self.event.image else ''
        if self.package_id:
            return self.package.image.url if self.package.image else ''
        ref = self._item_ref
        if ref:
            _name, kind, slug = ref
            if kind == 'experience':
                obj = Experience.objects.filter(slug=slug).first()
                if obj:
                    if obj.image:
                        return obj.image.url
                    if obj.static_image:
                        return static(obj.static_image)
            else:
                obj = Destination.objects.filter(slug=slug).first()
                if obj and obj.image:
                    return obj.image.url
        return ''

    @property
    def display_date(self):
        if self.event_id:
            return '%s | %s' % (self.event.date_label, self.event.time_label)
        if self.preferred_date:
            return self.preferred_date.strftime('%a %d %b %Y')
        return ''

    @property
    def display_place(self):
        if self.event_id:
            return self.event.location_name
        if self.package_id:
            return getattr(self.package, 'location', '') or ''
        ref = self._item_ref
        if ref:
            _name, kind, slug = ref
            if kind == 'experience':
                obj = Experience.objects.filter(slug=slug).first()
                import re as _re
                _pm = _re.search(r'(?m)^Place: (.+)$', self.special_requests or '')
                if _pm:
                    return _pm.group(1).strip()
                return obj.location if obj else ''
            obj = Destination.objects.select_related('region').filter(slug=slug).first()
            return obj.region.name if obj else ''
        return ''



class Payment(models.Model):
    # DEMO ONLY: we never store full card numbers or CVV, only the last 4 digits.
    class Method(models.TextChoices):
        JUICE = 'juice', 'JUICE by MCB'
        CARD = 'card', 'Credit Card (Visa/Mastercard)'
        MYT = 'myt', 'My.T Money'
        QR = 'qr', 'Scan to Pay'

    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        PAID = 'paid', 'Paid'
        FAILED = 'failed', 'Failed'

    booking = models.OneToOneField(Booking, on_delete=models.CASCADE, related_name='payment')
    method = models.CharField(max_length=10, choices=Method.choices)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    card_last4 = models.CharField(max_length=4, blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f'{self.booking.reference} - {self.get_status_display()}'


def _set_booking_display_title(self, value):
    self.__dict__['_display_title'] = value


Booking.display_title = Booking.display_title.setter(_set_booking_display_title)


class GalleryPhoto(models.Model):
    """An extra picture for the photo slideshow on an experience or place page."""
    experience = models.ForeignKey('explore.Experience', null=True, blank=True,
                                   on_delete=models.CASCADE, related_name='gallery_photos')
    destination = models.ForeignKey('explore.Destination', null=True, blank=True,
                                    on_delete=models.CASCADE, related_name='gallery_photos')
    image = models.ImageField(upload_to='gallery/')
    order = models.PositiveIntegerField(default=0, help_text='Smaller numbers show first')

    class Meta:
        ordering = ['order', 'id']

    def __str__(self):
        owner = self.experience or self.destination
        return 'Photo %s for %s' % (self.pk, owner)


class FoodSpot(models.Model):
    """A place (restaurant, stall, market) where a food experience can be tried."""
    experiences = models.ManyToManyField('explore.Experience', related_name='food_spots', blank=True,
                                         help_text='The dishes this place serves')
    name = models.CharField(max_length=120)
    area = models.CharField(max_length=100, blank=True, help_text='e.g. Port Louis')
    price_range = models.CharField(max_length=50, blank=True, help_text='e.g. Rs 100 - 300')
    note = models.CharField(max_length=200, blank=True, help_text='Short tip, e.g. Open mornings only')
    map_url = models.URLField(blank=True, help_text='Google Maps link (optional)')
    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order', 'name']

    def __str__(self):
        return self.name


# map-pins
class MapPin(models.Model):
    """An extra pin on the Location map of a place or an experience."""
    destination = models.ForeignKey('Destination', null=True, blank=True, on_delete=models.CASCADE, related_name='map_pins')
    experience = models.ForeignKey('Experience', null=True, blank=True, on_delete=models.CASCADE, related_name='map_pins')
    name = models.CharField(max_length=120, help_text='Shown when the pin is clicked, e.g. Central Market, Port Louis')
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order', 'id']

    def __str__(self):
        return self.name


# chosen-place
def _booking_chosen_place(self):
    import re
    mt = re.search(r'(?m)^Place: (.+)$', self.special_requests or '')
    return mt.group(1).strip() if mt else ''


def _booking_chosen_time(self):
    import re
    mt = re.search(r'(?m)^Preferred time: (\S+)', self.special_requests or '')
    return mt.group(1) if mt else ''


Booking.chosen_place = property(_booking_chosen_place)
Booking.chosen_time = property(_booking_chosen_time)


# lifecycle
def _booking_lifecycle(self):
    from django.utils import timezone
    d = self.preferred_date
    if d is None and self.event_id:
        d = getattr(self.event, 'date', None)
    if d is None:
        return None
    n = (d - timezone.localdate()).days
    if n > 0:
        return {'state': 'upcoming', 'days': n, 'date': d}
    if n == 0:
        return {'state': 'today', 'days': 0, 'date': d}
    return {'state': 'completed', 'days': -n, 'date': d}


Booking.lifecycle = property(_booking_lifecycle)


class TransportOption(models.Model):
    """How to get to a place: bus, metro, taxi, rental. Entered in the admin on each place."""
    KIND_CHOICES = [
        ('own', 'Own transport'), ('taxi', 'Taxi'), ('car', 'Car'), ('bus', 'Bus'),
    ]
    destination = models.ForeignKey('explore.Destination', on_delete=models.CASCADE, related_name='transport_options', null=True, blank=True, help_text='Leave empty for the default rows, shown on events that have no place of their own.')
    kind = models.CharField(max_length=20, choices=KIND_CHOICES, default='bus')
    from_where = models.CharField(max_length=120, blank=True, help_text='Starting point, e.g. Port Louis or the airport')
    duration = models.CharField(max_length=60, blank=True, help_text='e.g. about 1h 30')
    price_text = models.CharField(max_length=60, blank=True, help_text='e.g. about Rs 80')
    details = models.TextField(blank=True, help_text='Bus number, stop name, tips...')
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['order', 'id']
        verbose_name = 'transport option'

    def __str__(self):
        return '%s - %s' % (self.destination or 'Default (events without a place)', self.get_kind_display())


def transport_rows(destination=None):
    """Transport rows of a real place, else the default rows (rows with no place)."""
    rows = []
    pk = getattr(destination, 'pk', None)
    if pk:
        rows = list(TransportOption.objects.filter(destination_id=pk))
    if not rows:
        rows = list(TransportOption.objects.filter(destination__isnull=True))
    return rows


def _event_transport_options(self):
    return transport_rows(self.destination)


Event.transport_for_page = property(_event_transport_options)


def _food_parts(self):
    """Split long_description into the overview text and the Taste/Dietary lines."""
    text = (self.long_description or '').replace('\r\n', '\n')
    lines = text.split('\n')
    for i, ln in enumerate(lines):
        if ln.strip().lower().startswith(('taste:', 'dietary:')):
            return '\n'.join(lines[:i]).strip(), '\n'.join(lines[i:]).strip()
    return text.strip(), ''


Experience.food_overview = property(lambda self: _food_parts(self)[0])
Experience.food_facts = property(lambda self: _food_parts(self)[1])
