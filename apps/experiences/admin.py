
from django.contrib import admin

from .models import Category, ChatMessage, ChatSession, Event, Favourite, Experience, FAQEntry, Review


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
    list_display = ('title', 'date', 'start_time', 'destination', 'category', 'difficulty', 'price', 'capacity', 'is_featured', 'show_on_explore', 'show_on_calendar', 'calendar_section')
    list_filter = ('category', 'difficulty', 'is_featured', 'show_on_explore', 'show_on_calendar', 'calendar_section', 'date', 'destination__region')
    list_editable = ('is_featured', 'show_on_explore', 'show_on_calendar', 'calendar_section')
    search_fields = ('title', 'location_name')
    date_hierarchy = 'date'
    prepopulated_fields = {'slug': ('title',)}
    inlines = [ReviewInline]
    fieldsets = (
        ('What customers book', {
            'fields': ('title', 'slug', 'category', 'destination', 'date', 'start_time', 'end_time',
                       'price', 'premium_price', 'standard_package_label', 'premium_package_label',
                       'capacity', 'is_featured', 'show_on_explore', 'show_on_calendar', 'calendar_section'),
        }),
        ('Experience Insight page content (all shown from here - nothing hardcoded)', {
            'description': 'Header card: location_name, difficulty, guide + guide review count. '
                           'Overview tab: pickup_details, group_size_label, languages_supported, cancellation_policy. '
                           'Inclusions / Itinerary / Location / Guide tabs: inclusions, itinerary_text, destination map, guide.',
            'fields': ('short_description', 'description', 'image', 'image_credit',
                       'gallery_image_1', 'gallery_image_1_credit',
                       'gallery_image_2', 'gallery_image_2_credit',
                       'gallery_image_3', 'gallery_image_3_credit',
                       'location_name', 'difficulty', 'guide',
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
    list_display = ('user', 'event', 'created_at')
    list_filter = ('event',)
    search_fields = ('user__username', 'event__title')


class ChatMessageInline(admin.TabularInline):
    model = ChatMessage
    extra = 1
    readonly_fields = ['created_at']


@admin.register(ChatSession)
class ChatSessionAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'is_live_requested', 'is_resolved', 'created_at']
    list_filter = ['is_live_requested', 'is_resolved']
    inlines = [ChatMessageInline]


@admin.register(FAQEntry)
class FAQEntryAdmin(admin.ModelAdmin):
    list_display = ['keyword', 'answer']


@admin.register(Experience)
class ExperienceAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'kind', 'location', 'rating', 'price', 'order', 'is_active')
    list_filter = ('category', 'kind', 'difficulty', 'is_active')
    list_editable = ('order', 'is_active')
    search_fields = ('name', 'location', 'kind')
    prepopulated_fields = {'slug': ('name',)}
