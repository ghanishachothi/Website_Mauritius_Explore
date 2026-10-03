
from django.contrib import admin

from .models import Category,ChatMessage,ChatSession, Event, Favourite, Experience, FAQEntry


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('title', 'date', 'start_time', 'destination', 'category', 'price', 'capacity', 'is_featured', 'show_on_calendar', 'calendar_section')
    list_filter = ('category', 'is_featured', 'show_on_calendar', 'calendar_section', 'date', 'destination__region')
    list_editable = ('is_featured', 'show_on_calendar', 'calendar_section')
    search_fields = ('title', 'location_name')
    date_hierarchy = 'date'
    prepopulated_fields = {'slug': ('title',)}


@admin.register(Favourite)
class FavouriteAdmin(admin.ModelAdmin):
    list_display = ('user', 'event', 'created_at')
    list_filter = ('event',)
    search_fields = ('user__username', 'event__title')

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('user', 'event', 'rating', 'created_at')

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
