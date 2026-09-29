from django.urls import path
from django.views.generic import RedirectView

from . import views

app_name = 'experiences'

urlpatterns = [
    path('', views.all_events, name='all_events'),
    path('experience-insight/', views.experience_insight, name='experience_insight'),
    path('explore-your-way/', RedirectView.as_view(pattern_name='explore', permanent=False), name='explore_your_way'),
    path('calendar/', views.island_calendar, name='island_calendar'),
    path('my-experiences/', views.my_experiences, name='my_experiences'),
    path('<slug:slug>/', views.event_detail, name='event_detail'),  # keep this LAST
]
