from django.urls import path
from django.views.generic import TemplateView
from . import views
from django.contrib.auth import views as auth_views
from django.urls import path, reverse_lazy
from .forms import CustomSetPasswordForm
from django.conf import settings
from django.conf.urls.static import static


# ======================================================================
# from the old "core" app
# ======================================================================

core_patterns = [
    path('', views.home, name='home'),
    path('contact/', views.contact, name='contact'),            # POST from the Help pop-up
    path('app-waitlist/', views.app_waitlist, name='app_waitlist'),
    path('manifest.webmanifest', views.manifest, name='manifest'),
    path('sw.js', views.service_worker, name='service_worker'),
    path('help/', views.contact_page, name='help'),
    path('privacy/', TemplateView.as_view(template_name='core/privacy.html', extra_context={'doc_title': 'Privacy Policy'}), name='privacy'),
    path('terms/', TemplateView.as_view(template_name='core/terms.html', extra_context={'doc_title': 'Terms of Service'}), name='terms'),
]


# ======================================================================
# from the old "users" app
# ======================================================================

users_patterns = [
    # Auth & Registration
    path('signup/', views.signup, name='signup'),
    path('login/', auth_views.LoginView.as_view(template_name='users/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('change-password/', views.change_password, name='change_password'),
    path('request-delete-account/', views.request_delete_account, name='request_delete_account'),

    # Password Reset (Using DevPasswordResetView for direct browser redirection)
    path(
        'password-reset/',
        views.DevPasswordResetView.as_view(),
        name='password_reset'
    ),

    path(
        'password-reset/done/',
        auth_views.PasswordResetDoneView.as_view(
            template_name='users/password_reset_done.html'
        ),
        name='password_reset_done'
    ),

    path(
        'password-reset-confirm/<uidb64>/<token>/',
        auth_views.PasswordResetConfirmView.as_view(
            template_name='users/password_reset_confirm.html',
            form_class=CustomSetPasswordForm,
            success_url=reverse_lazy('users:password_reset_complete')
        ),
        name='password_reset_confirm'
    ),

    path(
        'password-reset-complete/',
        auth_views.PasswordResetCompleteView.as_view(
            template_name='users/password_reset_complete.html'
        ),
        name='password_reset_complete'
    ),

    # Profile management
    path('profile/', views.profile, name='profile'),
]


# ======================================================================
# from the old "destinations" app
# ======================================================================

destinations_patterns = [
    path('', views.explore_island, name='explore_island'),
    path('experience-finder/', views.experience_finder, name='experience_finder'),
    path('suggest/', views.send_suggestion, name='suggest'),
    path('map/', views.island_map, name='map'),
    path('board/', views.explore_board, name='explore_board'),
    path('guides-packages/', views.guides_packages, name='guides_packages'),
    path('guides/<slug:slug>/', views.guide_detail, name='guide_detail'),
    path('region/<slug:slug>/', views.region_detail, name='region_detail'),

    #path('reserve-experience/', views.destinations_reserve_experience, name='reserve_experience'),
    path('place/<slug:slug>/', views.destination_detail, name='destination_detail'),
]


# ======================================================================
# from the old "experiences" app
# ======================================================================

experiences_patterns = [
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

    path('bookings/<int:pk>/cancel/', views.cancel_booking, name='cancel_booking'),
    path('reviews/add/', views.add_review, name='add_review'),
    path('reviews/<int:pk>/edit/', views.edit_review, name='edit_review'),
    path('reviews/<int:pk>/delete/', views.delete_review, name='delete_review'),
    path('favourites/<int:pk>/toggle/', views.toggle_favourite, name='toggle_favourite'),
    path('favourites/by-slug/<slug:slug>/toggle/', views.toggle_favourite, name='toggle_favourite_by_slug'),

    path('<slug:slug>/', views.event_detail, name='event_detail'),  # keep this LAST

]

if settings.DEBUG:
    experiences_patterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


# ======================================================================
# from the old "bookings" app
# ======================================================================

bookings_patterns = [
    path('reserve/<slug:slug>/', views.reserve, name='reserve'),
    path('reserve-experience/', views.reserve_experience, name='reserve_experience'),
    path('checkout/<str:reference>/', views.checkout, name='checkout'),
    path('confirmation/<str:reference>/', views.confirmation, name='confirmation'),
]


# ======================================================================
# from the old "admin_dashboard" app
# ======================================================================

admin_dashboard_patterns = [
    path('', views.dashboard, name='dashboard'),
]
