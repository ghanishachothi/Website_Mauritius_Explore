from django.contrib import admin

from .models import Category, Event


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('title', 'date', 'start_time', 'destination', 'category', 'price', 'capacity', 'is_featured')
    list_filter = ('category', 'is_featured', 'date', 'destination__region')
    list_editable = ('is_featured',)
    search_fields = ('title', 'location_name')
    date_hierarchy = 'date'
    prepopulated_fields = {'slug': ('title',)}


from .models import FoodExperience  # noqa: E402


@admin.register(FoodExperience)
class FoodExperienceAdmin(admin.ModelAdmin):
    list_display = ('name', 'kind', 'location', 'rating', 'price', 'order', 'is_active')
    list_filter = ('kind', 'is_active')
    list_editable = ('order', 'is_active')
    search_fields = ('name', 'location')
    prepopulated_fields = {'slug': ('name',)}
