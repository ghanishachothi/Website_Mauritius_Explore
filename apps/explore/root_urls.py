from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from apps.explore import urls as explore_urls
from apps.explore import views as destination_views

admin.site.site_header = 'Mauritius Explore Admin'
admin.site.site_title = 'Mauritius Explore Admin'
admin.site.index_title = 'Manage the website content'

urlpatterns = [
    path('admin/', admin.site.urls),
    path('explore-the-island/', destination_views.explore_island, name='explore_the_island'),
    path('', include((explore_urls.core_patterns, 'core'))),
    path('accounts/', include((explore_urls.users_patterns, 'users'))),
    path('explore/', destination_views.destinations_explore_your_way, name='explore'),
    path('explore-island/', destination_views.explore_island, name='explore_island'),
    path('regions/<slug:slug>/', destination_views.region_detail, name='region_showcase'),
    path('destinations/', include((explore_urls.destinations_patterns, 'destinations'))),
    path('experiences/', include((explore_urls.experiences_patterns, 'experiences'))),
    path('bookings/', include((explore_urls.bookings_patterns, 'bookings'))),
    path('dashboard/', include((explore_urls.admin_dashboard_patterns, 'admin_dashboard'))),
    path('accounts/', include('django.contrib.auth.urls')),
]

# Serve uploaded photos while developing
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
