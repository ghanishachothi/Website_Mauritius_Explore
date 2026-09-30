"""
Shared template context for base.html: navbar links, page links, account box, footer links.
Everything comes from the database (managed in /admin/ under Core) - nothing hardcoded.
"""
from django.urls import reverse, resolve
from django.urls.exceptions import NoReverseMatch


# Pages where a navbar link should stay highlighted, e.g. the Experience
# Insight link stays active while reading a single event's detail page.
SECTION_ALIASES = {
    'experience_insight': {'experience_insight', 'all_events', 'event_detail', 'explore_your_way'},
}


def _resolve_url(url_name, fallback='#'):
    """Turn a URL name like 'core:home' into a real path. Bad names fall back to '#'."""
    if not url_name:
        return fallback
    try:
        return reverse(url_name)
    except NoReverseMatch:
        return fallback


def site_navigation(request):
    """Navbar links, the account dropdown, and footer columns for base.html."""
    from apps.core.models import LegalLink, NavLink, SocialLink

    current_url_name = ''
    if request.resolver_match:
        current_url_name = request.resolver_match.url_name or ''

    nav_links = []
    for link in NavLink.objects.filter(is_active=True):
        url = _resolve_url(link.url_name)
        is_active = False
        try:
            link_url_name = resolve(url).url_name
        except NoReverseMatch:
            link_url_name = ''
        if link_url_name and link_url_name == current_url_name:
            is_active = True
        elif current_url_name in SECTION_ALIASES.get(link_url_name, set()):
            is_active = True
        nav_links.append({'label': link.label, 'url': url, 'is_active': is_active})

    page_links = {
        'home': _resolve_url('core:home'),
        'profile': _resolve_url('users:profile'),
        'my_experiences': _resolve_url('experiences:my_experiences'),
        'login': _resolve_url('users:login'),
        'create_account': _resolve_url('users:signup'),
        'logout': _resolve_url('users:logout'),
    }

    user = request.user
    account = None
    if user.is_authenticated:
        role = ''
        if hasattr(user, 'profile'):
            role = user.profile.get_role_display()
        account = {
            'full_name': user.get_full_name() or user.username,
            'email': user.email or user.username,
            'username': user.username,
            'role': role,
            'member_since': user.date_joined,
        }

    return {
        'nav_links': nav_links,
        'page_links': page_links,
        'account': account,
        'social_links': SocialLink.objects.filter(is_active=True),
        'legal_links': [
            {'label': link.label, 'url': link.url or '#'}
            for link in LegalLink.objects.filter(is_active=True)
        ],
    }
