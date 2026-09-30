from django.contrib import admin

from .models import ContactMessage, LegalLink, NavLink, SocialLink


@admin.register(NavLink)
class NavLinkAdmin(admin.ModelAdmin):
    list_display = ('label', 'url_name', 'order', 'is_active')
    list_editable = ('order', 'is_active')
    list_display_links = ('label',)
    search_fields = ('label', 'url_name')


@admin.register(SocialLink)
class SocialLinkAdmin(admin.ModelAdmin):
    list_display = ('platform', 'url', 'order', 'is_active')
    list_editable = ('order', 'is_active')
    list_display_links = ('platform',)


@admin.register(LegalLink)
class LegalLinkAdmin(admin.ModelAdmin):
    list_display = ('label', 'url', 'order', 'is_active')
    list_editable = ('order', 'is_active')
    list_display_links = ('label',)
    search_fields = ('label',)


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'subject', 'is_read', 'created_at')
    list_filter = ('is_read',)
    search_fields = ('name', 'email', 'subject')
