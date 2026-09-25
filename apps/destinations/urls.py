from django.urls import path

from . import views

app_name = 'destinations'

urlpatterns = [
    path('', views.explore_island, name='explore_island'),
    path('board/', views.explore_board, name='explore_board'),
    path('guides-packages/', views.guides_packages, name='guides_packages'),
    path('guides/<slug:slug>/', views.guide_detail, name='guide_detail'),
    path('region/<slug:slug>/', views.region_detail, name='region_detail'),
    path('place/<slug:slug>/', views.destination_detail, name='destination_detail'),
]
