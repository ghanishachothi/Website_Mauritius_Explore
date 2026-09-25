from django.shortcuts import get_object_or_404, render
from django.utils import timezone

from apps.experiences.models import Event

from .models import Destination, Guide, Package, Region


def explore_island(request):
    """Explore the Island page (regions + map)."""
    regions = Region.objects.prefetch_related('destinations')
    destinations = Destination.objects.select_related('region')
    map_points = [
        {'name': d.name, 'region': d.region.name,
         'lat': float(d.latitude), 'lng': float(d.longitude),
         'url': d.get_absolute_url()}
        for d in destinations if d.latitude is not None and d.longitude is not None
    ]
    return render(request, 'destinations/explore_island.html', {
        'regions': regions,
        'map_points': map_points,
    })


def region_detail(request, slug):
    """North / South / East / West / Central pages - ONE template for all five."""
    region = get_object_or_404(Region, slug=slug)
    events = Event.objects.filter(destination__region=region, date__gte=timezone.localdate())[:6]
    return render(request, 'destinations/region_detail.html', {
        'region': region,
        'destinations': region.destinations.all(),
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
