import json

from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.templatetags.static import static
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

# Apps talk to each other just by importing each other's models:
from apps.destinations.models import Destination
from apps.experiences.models import Event

from .forms import ContactForm, WaitlistForm
from .models import AppWaitlist, MonthTip, SitePage


def home(request):
    """Discover Mauritius homepage: hero, search, "When to come" and Top Destinations."""
    # --- Top Destinations carousel (featured places first) ---
    destinations = []
    for place in Destination.objects.select_related('region').filter(is_featured=True).order_by('order', 'name')[:12]:
        destinations.append({
            'name': place.name,
            'area': place.area or place.region.name,
            'url': place.get_absolute_url(),
            'image_url': place.image.url if place.image else static('images/combined-image__3_.jpg'),
        })

    # --- "When to come" planner ---
    tips = list(MonthTip.objects.all())
    months = [{'month': t.month, 'short_name': t.short_name} for t in tips]
    month_data = [{
        'month': t.month, 'name': t.name, 'headline': t.headline,
        'air': t.air, 'sea': t.sea, 'crowd': t.crowd,
        'note': t.note, 'highlight': t.highlight,
    } for t in tips]

    # --- what the search bar can find ---
    search_items = []
    for place in Destination.objects.select_related('region'):
        search_items.append({
            'group': 'Places', 'kind': 'place', 'name': place.name,
            'note': place.region.name, 'url': place.get_absolute_url(),
            'keys': f'{place.region.name} {place.short_description}',
        })
    for event in Event.objects.filter(date__gte=timezone.localdate()).select_related('category', 'destination'):
        search_items.append({
            'group': 'Events', 'kind': 'event', 'name': event.title,
            'note': event.date.strftime('%d %b'), 'url': event.get_absolute_url(),
            'keys': ' '.join(filter(None, [
                event.category.name if event.category else '',
                event.destination.name if event.destination else '',
                event.short_description,
            ])),
        })
    for page in SitePage.objects.filter(frame_ready=True):
        search_items.append({
            'group': 'Pages', 'kind': 'page', 'name': page.name,
            'note': '', 'url': page.url, 'keys': page.keywords,
        })

    return render(request, 'core/home.html', {
        'destinations': destinations,
        'months': months,
        'month_data': month_data,
        'search_items': search_items,
        'calendar_url': reverse('experiences:island_calendar'),
    })


@require_POST
def contact(request):
    """Help & Contact pop-up. Saves into ContactMessage and answers in JSON."""
    form = ContactForm(request.POST)
    if form.is_valid():
        form.save()
        return JsonResponse({'ok': True})
    return JsonResponse({'ok': False, 'error': 'Please fill in your name, a valid email and your message.'})


@require_POST
def app_waitlist(request):
    """"Notify me" in the app panel. Saves into AppWaitlist and answers in JSON."""
    form = WaitlistForm(request.POST)
    if form.is_valid():
        AppWaitlist.objects.get_or_create(email=form.cleaned_data['email'],
                                          store=form.cleaned_data['store'] or 'any')
        return JsonResponse({'ok': True})
    return JsonResponse({'ok': False, 'error': 'Please enter a valid email address.'})


def manifest(request):
    """Lets phones install the site like an app (Add to Home Screen)."""
    data = {
        'name': 'Mauritius Explorer',
        'short_name': 'Mauritius',
        'start_url': '/',
        'scope': '/',
        'display': 'standalone',
        'background_color': '#ffffff',
        'theme_color': '#10276B',
        'icons': [{'src': static('images/app/icon-192.png'), 'sizes': '192x192', 'type': 'image/png'}],
    }
    return HttpResponse(json.dumps(data), content_type='application/manifest+json')


SERVICE_WORKER_JS = """
// Minimal service worker: needed so browsers offer "Add to home screen".
self.addEventListener('install', () => self.skipWaiting());
self.addEventListener('activate', event => event.waitUntil(self.clients.claim()));
self.addEventListener('fetch', () => {});
"""


def service_worker(request):
    response = HttpResponse(SERVICE_WORKER_JS, content_type='application/javascript')
    response['Service-Worker-Allowed'] = '/'
    return response


def contact_page(request):
    """Old /contact/ links: open the homepage with the Help pop-up."""
    return redirect(reverse('core:home') + '#help')
