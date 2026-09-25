from django.contrib import messages
from django.shortcuts import redirect, render
from django.utils import timezone

# Apps talk to each other just by importing each other's models:
from apps.destinations.models import Destination, Region
from apps.experiences.models import Event

from .forms import ContactForm


def home(request):
    """Discover Mauritius homepage."""
    today = timezone.localdate()
    context = {
        'regions': Region.objects.all(),
        'featured_destinations': Destination.objects.filter(is_featured=True)[:6],
        'featured_events': Event.objects.filter(is_featured=True, date__gte=today)[:6],
    }
    return render(request, 'core/home.html', context)


def contact(request):
    form = ContactForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Thanks! We will get back to you soon.')
        return redirect('core:contact')
    return render(request, 'core/contact.html', {'form': form})
