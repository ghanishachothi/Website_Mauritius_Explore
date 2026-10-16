from django import forms
from django.contrib import admin

from .models import Destination, Guide, HeroTile, Package, Region, RegionHighlight,  Review, Suggestion, WayToExplore


class RegionHighlightInline(admin.TabularInline):
    model = RegionHighlight
    extra=1



class PlaceInline(admin.TabularInline):
    model = Destination
    fields = ('name', 'note', 'keywords', 'is_featured')
    extra = 1
    show_change_link = True

    def get_fields(self, request, obj=None):
        if obj and obj.slug == 'east':
            return (
                'name', 'short_description', 'image', 'area', 'order',
                'note', 'keywords', 'is_featured',
            )
        return self.fields


class ReviewInline(admin.TabularInline):
    model = Review
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
    inlines = [ReviewInline]
    search_fields = ('name', 'bio', 'languages')
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Package)
class PackageAdmin(admin.ModelAdmin):
    list_display = ('title', 'guide', 'price', 'rating', 'is_featured')
    list_filter = ('is_featured', 'guide')
    filter_horizontal = ('destinations', 'eligible_guides')
    prepopulated_fields = {'slug': ('title',)}


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('traveller_name', 'guide', 'rating', 'date')
