from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

admin.site.site_header = 'Mauritius Explore Admin'
admin.site.site_title = 'Mauritius Explore Admin'
admin.site.index_title = 'Manage the website content'

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('apps.core.urls')),
    path('accounts/', include('apps.users.urls')),
    path('destinations/', include('apps.destinations.urls')),
    path('experiences/', include('apps.experiences.urls')),
    path('bookings/', include('apps.bookings.urls')),
    path('dashboard/', include('apps.admin_dashboard.urls')),
]

# Serve uploaded photos while developing
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
