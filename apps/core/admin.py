from django.contrib import admin

from .models import (AppLink, AppWaitlist, ContactMessage, FooterColumn, FooterLink,
                     MonthTip, SitePage, SocialLink)


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