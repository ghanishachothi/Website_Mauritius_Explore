from django.urls import path

from . import views

from django.conf import settings
from django.conf.urls.static import static

app_name = 'experiences'

urlpatterns = [
    path('', views.all_events, name='all_events'),
    path('calendar/', views.island_calendar, name='island_calendar'),
    path('my-experiences/', views.my_experiences, name='my_experiences'),
    #path('food/', views.taste_mauritius, name='food'),
    path('my-experiences/', views.my_experiences, name='my_experiences'),
    path('my-experiences/review/add/', views.add_review, name='add_review'),
    path('my-experiences/review/<int:pk>/edit/', views.edit_review, name='edit_review'),
    path('my-experiences/review/<int:pk>/delete/', views.delete_review, name='delete_review'),
    path('my-experiences/favourite/<int:event_pk>/toggle/', views.toggle_favourite, name='toggle_favourite'),
    path('my-experiences/booking/<int:pk>/cancel/', views.cancel_booking, name='cancel_booking'),
    path('<slug:slug>/', views.event_detail, name='event_detail'),  # keep this LAST
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)