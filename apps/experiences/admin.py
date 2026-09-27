from django.contrib import admin

from .models import Category, Event


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('title', 'date', 'start_time', 'destination', 'category', 'price', 'capacity', 'is_featured', 'show_on_calendar', 'calendar_section')
    list_filter = ('category', 'is_featured', 'show_on_calendar', 'calendar_section', 'date', 'destination__region')
    list_editable = ('is_featured', 'show_on_calendar', 'calendar_section')
    search_fields = ('title', 'location_name')
    date_hierarchy = 'date'
    prepopulated_fields = {'slug': ('title',)}