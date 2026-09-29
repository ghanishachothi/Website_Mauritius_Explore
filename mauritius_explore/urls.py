from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from apps.destinations import views as destination_views

admin.site.site_header = 'Mauritius Explore Admin'
admin.site.site_title = 'Mauritius Explore Admin'
admin.site.index_title = 'Manage the website content'

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('apps.core.urls')),
    path('accounts/', include('apps.users.urls')),
    path('explore/', destination_views.explore_your_way, name='explore'),
    path('explore-island/', destination_views.explore_island, name='explore_island'),
    path('regions/<slug:slug>/', destination_views.region_detail, name='region_showcase'),
    path('destinations/', include('apps.destinations.urls')),
    path('experiences/', include('apps.experiences.urls')),
    path('bookings/', include('apps.bookings.urls')),
    path('dashboard/', include('apps.admin_dashboard.urls')),
]

# Serve uploaded photos while developing
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
