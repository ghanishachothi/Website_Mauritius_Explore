from django.urls import path

from . import views

app_name = 'core'

urlpatterns = [
    path('', views.home, name='home'),
    path('contact/', views.contact, name='contact'),            # POST from the Help pop-up
    path('app-waitlist/', views.app_waitlist, name='app_waitlist'),
    path('manifest.webmanifest', views.manifest, name='manifest'),
    path('sw.js', views.service_worker, name='service_worker'),
    path('help/', views.contact_page, name='help'),
]