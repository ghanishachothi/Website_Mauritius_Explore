from django.contrib import admin

from .models import Category, Event, Favourite, FoodExperience


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('title', 'date', 'start_time', 'destination', 'category', 'price', 'capacity', 'is_featured', 'show_on_calendar', 'calendar_section')
    list_filter = ('category', 'is_featured', 'show_on_calendar', 'calendar_section', 'date', 'destination__region')
    list_editable = ('is_featured', 'show_on_calendar', 'calendar_section')
    search_fields = ('title', 'location_name')
    date_hierarchy = 'date'
<<<<<<< HEAD
    prepopulated_fields = {'slug': ('title',)}


@admin.register(Favourite)
class FavouriteAdmin(admin.ModelAdmin):
    list_display = ('user', 'event', 'created_at')
    list_filter = ('event',)
    search_fields = ('user__username', 'event__title')


@admin.register(FoodExperience)
class FoodExperienceAdmin(admin.ModelAdmin):
    list_display = ('name', 'kind', 'location', 'rating', 'price', 'order', 'is_active')
    list_filter = ('kind', 'is_active')
    list_editable = ('order', 'is_active')
    search_fields = ('name', 'location')
    prepopulated_fields = {'slug': ('name',)}
=======
    prepopulated_fields = {'slug': ('title',)}
>>>>>>> 777b5135009dc1a3a6aa938759cdc06788176f5c
