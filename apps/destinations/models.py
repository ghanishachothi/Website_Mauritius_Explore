from django.db import models
from django.urls import reverse
from django.utils.text import slugify


class Region(models.Model):
    """North, South, East, West, Central."""
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(unique=True, blank=True)
    tagline = models.CharField(max_length=150, blank=True)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='regions/', blank=True)
    about_text = models.TextField(blank=True, help_text='"About the [Region]" paragraph')
    about_image = models.ImageField(upload_to='regions/about/', blank=True)
    travel_tip_image = models.ImageField(upload_to='regions/traveltip/', blank=True)
    travel_tip = models.TextField(blank=True, help_text='Travel Tip box text')
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
        return reverse('region_showcase', args=[self.slug])


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

    class Meta:
        ordering = ['name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('destinations:destination_detail', args=[self.slug])


class Guide(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, blank=True)
    photo = models.ImageField(upload_to='guides/', blank=True)
    bio = models.TextField(blank=True)
    languages = models.CharField(max_length=150, blank=True, help_text='e.g. English, French, Kreol')
    years_experience = models.PositiveIntegerField(default=0)
    rating = models.DecimalField(max_digits=2, decimal_places=1, default=5.0)
    review_count = models.PositiveIntegerField(default=0,
        help_text='Shown as "(68 reviews)" next to the guide on Experience Insight')
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
