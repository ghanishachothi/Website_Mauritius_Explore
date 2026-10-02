from django.urls import path

from . import views

from django.conf import settings
from django.conf.urls.static import static

app_name = 'experiences'

urlpatterns = [
    path('', views.all_events, name='all_events'),
    path('calendar/', views.island_calendar, name='island_calendar'),
    path('my-experiences/', views.my_experiences, name='my_experiences'),
    path('chat/start/', views.chat_start, name='chat_start'),
    path('chat/send/', views.chat_send, name='chat_send'),
    path('chat/request-agent/', views.chat_request_agent, name='chat_request_agent'),
    path('chat/poll/<int:session_id>/', views.chat_poll, name='chat_poll'),
    path('experience-insight/', views.experience_insight, name='experience_insight'),
    path('explore-your-way/', views.explore_your_way, name='explore_your_way'),
    path('category/<slug:category_slug>/', views.experience_category, name='experience_category'),
    path('<slug:slug>/', views.event_detail, name='event_detail'),  # keep this LAST
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)