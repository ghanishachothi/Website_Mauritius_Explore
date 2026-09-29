from django.contrib import admin

from .models import Category, Event
from .models import Experience

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'icon')
    prepopulated_fields = {'slug': ('name',)}

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('title', 'date', 'start_time', 'destination', 'category', 'price', 'capacity', 'is_featured')
    list_filter = ('category', 'is_featured', 'date', 'destination__region')
    list_editable = ('is_featured',)
    search_fields = ('title', 'location_name')
    date_hierarchy = 'date'
    prepopulated_fields = {'slug': ('title',)}

@admin.register(Experience)
class ExperienceAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'kind', 'location', 'rating', 'price', 'order', 'is_active')
    list_filter = ('category', 'kind', 'difficulty', 'is_active')
    list_editable = ('order', 'is_active')
    search_fields = ('name', 'location', 'kind')
    prepopulated_fields = {'slug': ('name',)}
