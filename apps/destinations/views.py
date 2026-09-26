from django.db.models import Prefetch
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from apps.experiences.models import Event

from .forms import SuggestionForm
from .models import Destination, Guide, HeroTile, Package, Region, WayToExplore


def _regions_with_places():
    """Every region with its places (A-Z) already loaded - used by several pages."""
    return Region.objects.prefetch_related(
        Prefetch('destinations', queryset=Destination.objects.order_by('name')))


def explore_island(request):
    """Explore the Island page: hero, ways to explore, regions, map, suggestions."""
    regions = list(_regions_with_places())
    ways = list(WayToExplore.objects.all())

    # "Find things to do": places first (grouped by region), then regions, then ways to explore
    search_items = (
        [{'kind': 'place', 'name': d.name, 'note': d.note, 'url': d.region_url,
          'region': r.list_title or r.name, 'keys': f'{d.note} {d.keywords} {d.area} {r.name}'}
         for r in regions for d in r.destinations.all()]
        + [{'kind': 'region', 'name': r.name, 'url': r.get_absolute_url(), 'keys': r.keywords}
           for r in regions]
        + [{'kind': 'way', 'name': w.title, 'url': w.url, 'keys': w.keywords} for w in ways]
    )

    return render(request, 'destinations/explore_island.html', {
        'hero_tiles': HeroTile.objects.all(),
        'ways': ways,
        'regions': regions,
        'search_items': search_items,
    })


@require_POST
def send_suggestion(request):
    """"Suggest an idea" pop-up: saves into Suggestion (read it in /admin/) and answers in JSON."""
    form = SuggestionForm(request.POST)
    if form.is_valid():
        form.save()
        return JsonResponse({'ok': True})
    if 'email' in form.errors:
        error = "That email doesn't look complete. Use a full address like name@gmail.com, or leave it empty."
    else:
        error = 'Please write your idea before sending.'
    return JsonResponse({'ok': False, 'error': error}, status=400)


def island_map(request):
    """Google Map frame (teammate). Every place with latitude/longitude is sent as map_points."""
    places = Destination.objects.select_related('region').exclude(latitude=None).exclude(longitude=None)
    map_points = [{
        'name': d.name, 'region': d.region.name, 'note': d.note,
        'lat': float(d.latitude), 'lng': float(d.longitude),
        'url': d.region_url, 'image': d.image.url if d.image else '',
    } for d in places]
    return render(request, 'destinations/map.html', {
        'regions': Region.objects.all(),
        'map_points': map_points,
    })


def region_detail(request, slug):
    """North / South / East / West / Central frames (teammates) - ONE template for all five.
    ?place=<slug> tells which place was clicked on Explore the Island."""
    region = get_object_or_404(Region, slug=slug)
    events = Event.objects.filter(destination__region=region, date__gte=timezone.localdate())[:6]
    return render(request, 'destinations/region_detail.html', {
        'region': region,
        'destinations': region.destinations.order_by('name'),
        'selected_place': request.GET.get('place', ''),
        'events': events,
    })


def destination_detail(request, slug):
    destination = get_object_or_404(Destination.objects.select_related('region'), slug=slug)
    return render(request, 'destinations/destination_detail.html', {
        'destination': destination,
        'events': destination.events.filter(date__gte=timezone.localdate()),
        'packages': destination.packages.all(),
    })


def guides_packages(request):
    """Guides & Packages page."""
    return render(request, 'destinations/guides_packages.html', {
        'guides': Guide.objects.filter(is_active=True),
        'packages': Package.objects.select_related('guide'),
    })


def guide_detail(request, slug):
    """Guide profile page (e.g. Aliyah C., John W.)."""
    guide = get_object_or_404(Guide, slug=slug, is_active=True)
    return render(request, 'destinations/guide_detail.html', {
        'guide': guide,
        'packages': guide.packages.all(),
    })


def explore_board(request):
    """Explore Board page, filterable by region: /destinations/board/?region=north"""
    destinations = Destination.objects.select_related('region')
    selected = request.GET.get('region')
    if selected:
        destinations = destinations.filter(region__slug=selected)
    return render(request, 'destinations/explore_board.html', {
        'destinations': destinations,
        'regions': Region.objects.all(),
        'selected_region': selected,
    })
