from django.contrib import admin

from .models import Destination, Guide, Package, Region


@admin.register(Region)
class RegionAdmin(admin.ModelAdmin):
    list_display = ('name', 'order')
    list_editable = ('order',)
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Destination)
class DestinationAdmin(admin.ModelAdmin):
    list_display = ('name', 'region', 'is_featured')
    list_filter = ('region', 'is_featured')
    list_editable = ('is_featured',)
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Guide)
class GuideAdmin(admin.ModelAdmin):
    list_display = ('name', 'role', 'rating', 'is_active')
    list_filter = ('is_active',)
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Package)
class PackageAdmin(admin.ModelAdmin):
    list_display = ('title', 'guide', 'price', 'rating', 'is_featured')
    list_filter = ('is_featured', 'guide')
    filter_horizontal = ('destinations',)
    prepopulated_fields = {'slug': ('title',)}
