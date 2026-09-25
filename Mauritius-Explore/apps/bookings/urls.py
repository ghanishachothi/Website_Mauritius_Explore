from django.urls import path

from . import views

app_name = 'bookings'

urlpatterns = [
    path('reserve/<slug:slug>/', views.reserve, name='reserve'),
    path('checkout/<str:reference>/', views.checkout, name='checkout'),
    path('confirmation/<str:reference>/', views.confirmation, name='confirmation'),
]
