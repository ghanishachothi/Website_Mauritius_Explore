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
    role = models.CharField(max_length=100, blank=True,
                             help_text="e.g. Marine Biology Expert. Shown under their name.")
    bio = models.TextField(blank=True)
    languages = models.CharField(max_length=150, blank=True, help_text='e.g. English, French, Kreol')
    years_experience = models.PositiveIntegerField(default=0)
    rating = models.DecimalField(max_digits=2, decimal_places=1, default=5.0)
    review_count = models.PositiveIntegerField(default=0)
    specialities = models.CharField(max_length=200, blank=True,
                                     help_text="Comma-separated tags, e.g. Snorkeling, Cruises, Marine life")
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
 
    @property
    def speciality_list(self):
        return [item.strip() for item in self.specialities.split(",") if item.strip()]
 
    @property
    def language_list(self):
        return [item.strip() for item in self.languages.split(",") if item.strip()]



class Package(models.Model):
    title = models.CharField(max_length=150)
    slug = models.SlugField(unique=True, blank=True)
    guide = models.ForeignKey(Guide, on_delete=models.SET_NULL, null=True, blank=True, related_name='packages')
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
 
    class Meta:
        ordering = ['title']
 
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)
 
    def __str__(self):
        return self.title
 
    @property
    def includes_list(self):
        return [line.strip() for line in self.includes.splitlines() if line.strip()]
 
    @property
    def display_languages(self):
        return self.languages or (self.guide.languages if self.guide else "")
 
    @property
    def search_text(self):
        return " ".join([self.title, self.description, self.includes]).lower()
 

