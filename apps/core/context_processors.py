"""
Gives EVERY page the data that base.html needs (header, side menu, footer,
app badges, social links, Help pop-up topics). Registered in settings.py.
Querysets are lazy: nothing is read from the database unless a template uses it.
"""
from django.urls import reverse
from django.utils.functional import SimpleLazyObject

from .models import AppLink, ContactMessage, FooterColumn, SitePage, SocialLink


def site_nav(request):
    return {
        'header_pages_1': SitePage.objects.filter(location=SitePage.Location.HEADER_1),
        'header_pages_2': SitePage.objects.filter(location=SitePage.Location.HEADER_2),
        'side_pages': SitePage.objects.filter(location=SitePage.Location.SIDE),
        'footer_columns': FooterColumn.objects.prefetch_related('links'),
        'app_links': AppLink.objects.all(),
        'social_links': SocialLink.objects.filter(show_in_footer=True),
        # {{ socials.whatsapp }} / {{ socials.gmail }} in the Help pop-up
        'socials': SimpleLazyObject(lambda: {s.platform: s.url for s in SocialLink.objects.all()}),
        'topics': ContactMessage.Topic.choices,
        'login_url': reverse('users:login'),
    }