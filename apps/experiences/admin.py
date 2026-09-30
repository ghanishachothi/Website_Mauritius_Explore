from django.contrib import admin

from .models import Category, Event, Favourite, Review


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('name',)}


class ReviewInline(admin.TabularInline):
    """Add reviews directly on the Event page - no need to hunt for a separate table."""
    model = Review
    extra = 1
    fields = ('user', 'rating', 'title', 'comment')


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('title', 'date', 'start_time', 'destination', 'category', 'difficulty', 'price', 'capacity', 'is_featured')
    list_filter = ('category', 'difficulty', 'is_featured', 'date', 'destination__region')
    list_editable = ('is_featured',)
    search_fields = ('title', 'location_name')
    date_hierarchy = 'date'
    prepopulated_fields = {'slug': ('title',)}
    inlines = [ReviewInline]
    fieldsets = (
        ('What customers book', {
            'fields': ('title', 'slug', 'category', 'destination', 'date', 'start_time', 'end_time',
                       'price', 'premium_price', 'standard_package_label', 'premium_package_label',
                       'capacity', 'is_featured'),
        }),
        ('Experience Insight page content (all shown from here - nothing hardcoded)', {
            'description': 'Header card: location_name, difficulty, guide + guide review count. '
                           'Overview tab: pickup_details, group_size_label, languages_supported, cancellation_policy. '
                           'Inclusions / Itinerary / Location / Guide tabs: inclusions, itinerary_text, destination map, guide.',
            'fields': ('short_description', 'description', 'image', 'gallery_image_1', 'gallery_image_2',
                       'gallery_image_3', 'location_name', 'difficulty', 'guide',
                       'rating', 'review_count', 'pickup_details', 'group_size_label', 'group_size_type',
                       'languages_supported', 'cancellation_policy', 'inclusions', 'itinerary_text'),
        }),
    )


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('event', 'user', 'rating', 'title', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('event__title', 'title', 'comment')


@admin.register(Favourite)
class FavouriteAdmin(admin.ModelAdmin):
    list_display = ('event', 'user', 'created_at')
    search_fields = ('event__title', 'user__username')
