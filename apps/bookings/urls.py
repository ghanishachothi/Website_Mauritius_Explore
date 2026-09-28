from django.urls import path

from . import views

app_name = 'bookings'

urlpatterns = [
    path('reserve/<slug:slug>/', views.reserve, name='reserve'),
    path('reserve-experience/', views.reserve_experience, name='reserve_experience'),
    path('checkout/', views.checkout_start, name='checkout_start'),
    path('checkout/<str:reference>/', views.checkout, name='checkout'),
    path('confirmation/<str:reference>/', views.confirmation, name='confirmation'),
]
