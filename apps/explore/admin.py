from django.contrib import admin
from .models import (AppLink, AppWaitlist, ContactMessage, FooterColumn, FooterLink,
                     MonthTip, SitePage, SocialLink)
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from .models import Profile
from django import forms
from .models import Destination, Guide, HeroTile, Package, Region, RegionHighlight,  GuideReview, Suggestion, WayToExplore
from .models import Category, ChatMessage, ChatSession, Event, Favourite, Experience, FAQEntry, Review
from .models import Booking, Payment


# ======================================================================
# from the old "core" app
# ======================================================================

@admin.register(SitePage)
class SitePageAdmin(admin.ModelAdmin):
    list_display = ('name', 'url', 'location', 'order', 'frame_ready')
    list_filter = ('location', 'frame_ready')
    list_editable = ('location', 'order', 'frame_ready')
    search_fields = ('name', 'url', 'keywords')


class FooterLinkInline(admin.TabularInline):
    model = FooterLink
    extra = 1


@admin.register(FooterColumn)
class FooterColumnAdmin(admin.ModelAdmin):
    list_display = ('title', 'order')
    list_editable = ('order',)
    inlines = [FooterLinkInline]


@admin.register(AppLink)
class AppLinkAdmin(admin.ModelAdmin):
    list_display = ('store', 'url', 'order')
    list_editable = ('url', 'order')


@admin.register(SocialLink)
class SocialLinkAdmin(admin.ModelAdmin):
    list_display = ('platform', 'url', 'icon', 'show_in_footer', 'order')
    list_editable = ('url', 'icon', 'show_in_footer', 'order')


@admin.register(MonthTip)
class MonthTipAdmin(admin.ModelAdmin):
    list_display = ('month', 'headline', 'air', 'sea', 'crowd')
    list_editable = ('headline', 'air', 'sea', 'crowd')


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'topic', 'is_read', 'created_at')
    list_filter = ('is_read', 'topic')
    list_editable = ('is_read',)
    search_fields = ('name', 'email', 'message')


@admin.register(AppWaitlist)
class AppWaitlistAdmin(admin.ModelAdmin):
    list_display = ('email', 'store', 'created_at')
    list_filter = ('store',)


# ======================================================================
# from the old "users" app
# ======================================================================

class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = True
    extra = 0


class CustomUserAdmin(UserAdmin):
    inlines = [ProfileInline]


admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'deletion_requested', 'phone_number', 'created_at')
    list_filter = ('deletion_requested', 'created_at')
    list_editable = ('deletion_requested',)
    actions = ['approve_deletion']

    @admin.action(description='Approve account deletion (Delete User)')
    def approve_deletion(self, request, queryset):
        deleted_count = 0
        for profile in queryset:
            profile.user.delete()  # Deleting User also deletes Profile via CASCADE
            deleted_count += 1
        self.message_user(request, f"Successfully approved and deleted {deleted_count} account(s).")


# ======================================================================
# from the old "destinations" app
# ======================================================================

class RegionHighlightInline(admin.TabularInline):
    model = RegionHighlight
    extra=1



class PlaceInline(admin.TabularInline):
    model = Destination
    fields = ('name', 'note', 'keywords', 'is_featured')
    extra = 1
    show_change_link = True


class GuideReviewInline(admin.TabularInline):
    model = GuideReview
    extra = 1


class RegionAdminForm(forms.ModelForm):
    class Meta:
        model = Region
        fields = '__all__'
        widgets = {
            'theme_color': forms.TextInput(attrs={'type': 'color'}),
            'card_color': forms.TextInput(attrs={'type': 'color'}),
            'accent_color': forms.TextInput(attrs={'type': 'color'}),
        }


@admin.register(Region)
class RegionAdmin(admin.ModelAdmin):
    form = RegionAdminForm
    list_display = ('name', 'tagline', 'is_wide', 'order')
    list_editable = ('tagline', 'order')
    prepopulated_fields = {'slug': ('name',)}
    inlines = [PlaceInline, RegionHighlightInline]


@admin.register(Destination)
class DestinationAdmin(admin.ModelAdmin):
    list_display = ('name', 'area', 'region', 'note', 'order', 'is_featured')
    list_filter = ('region', 'is_featured')
    list_editable = ('area', 'order', 'is_featured')
    search_fields = ('name', 'keywords', 'note')
    prepopulated_fields = {'slug': ('name',)}


@admin.register(HeroTile)
class HeroTileAdmin(admin.ModelAdmin):
    list_display = ('tag', 'text', 'color', 'order')
    list_editable = ('text', 'color', 'order')


@admin.register(WayToExplore)
class WayToExploreAdmin(admin.ModelAdmin):
    list_display = ('title', 'url', 'order')
    list_editable = ('url', 'order')


@admin.register(Suggestion)
class SuggestionAdmin(admin.ModelAdmin):
    list_display = ('idea', 'region', 'name', 'email', 'created_at', 'is_reviewed')
    list_filter = ('region', 'is_reviewed')
    list_editable = ('is_reviewed',)
    search_fields = ('idea', 'name', 'email')
    readonly_fields = ('name', 'email', 'region', 'idea', 'created_at')


@admin.register(Guide)
class GuideAdmin(admin.ModelAdmin):
    list_display = ('name', 'role', 'languages', 'rating', 'review_count', 'years_experience', 'is_active')
    list_filter = ('is_active',)
    inlines = [GuideReviewInline]
    search_fields = ('name', 'bio', 'languages')
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Package)
class PackageAdmin(admin.ModelAdmin):
    list_display = ('title', 'guide', 'price', 'rating', 'is_featured')
    list_filter = ('is_featured', 'guide')
    filter_horizontal = ('destinations', 'eligible_guides')
    prepopulated_fields = {'slug': ('title',)}


@admin.register(GuideReview)
class GuideReviewAdmin(admin.ModelAdmin):
    list_display = ('traveller_name', 'guide', 'rating', 'date')


# ======================================================================
# from the old "experiences" app
# ======================================================================

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'show_on_board', 'order')
    list_editable = ('show_on_board', 'order')
    prepopulated_fields = {'slug': ('name',)}


class ReviewInline(admin.TabularInline):
    """Add reviews directly on the Event page - no need to hunt for a separate table."""
    model = Review
    extra = 1
    fields = ('user', 'rating', 'title', 'comment')


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('title', 'date', 'start_time', 'destination', 'category', 'difficulty', 'price', 'capacity', 'is_featured', 'show_on_explore_your_way', 'show_on_explore_board', 'show_on_all_events', 'show_on_calendar', 'calendar_section')
    list_filter = ('category', 'difficulty', 'is_featured', 'show_on_explore_your_way', 'show_on_explore_board', 'show_on_all_events', 'show_on_calendar', 'calendar_section', 'date', 'destination__region')
    list_editable = ('is_featured', 'show_on_explore_your_way', 'show_on_explore_board', 'show_on_all_events', 'show_on_calendar', 'calendar_section')
    search_fields = ('title', 'location_name')
    date_hierarchy = 'date'
    prepopulated_fields = {'slug': ('title',)}
    inlines = [ReviewInline]
    fieldsets = (
        ('What customers book', {
            'fields': ('title', 'slug', 'category', 'destination', 'date', 'start_time', 'end_time',
                       'price', 'premium_price', 'standard_package_label', 'premium_package_label',
                       'capacity', 'is_featured', 'show_on_explore_your_way', 'show_on_explore_board', 'show_on_all_events', 'show_on_calendar', 'calendar_section'),
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


# ======================================================================
# from the old "bookings" app
# ======================================================================

class PaymentInline(admin.StackedInline):
    model = Payment
    extra = 0


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('reference', 'event', 'user', 'number_of_people', 'total_price', 'status', 'created_at')
    list_filter = ('status', 'event')
    search_fields = ('reference', 'full_name', 'email', 'user__username')
    readonly_fields = ('reference', 'total_price', 'created_at')
    inlines = [PaymentInline]


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('booking', 'method', 'amount', 'status', 'paid_at')
    list_filter = ('status', 'method')