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
from django.db import models
from django.templatetags.static import static
from django.urls import reverse
from django.utils.text import slugify


class Region(models.Model):
    """North, South, East, West, Central."""

    class Scrim(models.TextChoices):
        LIGHT = 'light', 'White fade'
        DARK = 'dark', 'Soft white fade'
        WIDE = 'wide', 'Sand fade (wide card)'

    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(unique=True, blank=True)
    tagline = models.CharField(max_length=150, blank=True, help_text='Short text on the region card')
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='regions/', blank=True, help_text='Upload a photo (optional)')
    static_image = models.CharField(max_length=200, blank=True,
                                    help_text='Used when no photo is uploaded, e.g. images/explore/regions/north.jpg')
    list_title = models.CharField(max_length=60, blank=True, help_text='Title in the "View all region" list')
    scrim = models.CharField(max_length=10, choices=Scrim.choices, default=Scrim.LIGHT,
                             help_text='How the photo fades into the text on the card')
    is_wide = models.BooleanField(default=False, help_text='Card takes the full width (Central)')
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


class Guide(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, blank=True)
    photo = models.ImageField(upload_to='guides/', blank=True)
    bio = models.TextField(blank=True)
    languages = models.CharField(max_length=150, blank=True, help_text='e.g. English, French, Kreol')
    years_experience = models.PositiveIntegerField(default=0)
    rating = models.DecimalField(max_digits=2, decimal_places=1, default=5.0)
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


class Package(models.Model):
    title = models.CharField(max_length=150)
    slug = models.SlugField(unique=True, blank=True)
    guide = models.ForeignKey(Guide, on_delete=models.SET_NULL, null=True, blank=True, related_name='packages')
    destinations = models.ManyToManyField(Destination, blank=True, related_name='packages')
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='packages/', blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    duration = models.CharField(max_length=50, blank=True, help_text='e.g. Half day, 3 days')
    is_featured = models.BooleanField(default=False)

    class Meta:
        ordering = ['title']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title


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
