from django.urls import path

from . import views

app_name = 'experiences'

urlpatterns = [
    path('', views.all_events, name='all_events'),
    path('calendar/', views.island_calendar, name='island_calendar'),
    path('my-experiences/', views.my_experiences, name='my_experiences'),
    path('food/', views.taste_mauritius, name='food'),
    path('<slug:slug>/', views.event_detail, name='event_detail'),  # keep this LAST
]
