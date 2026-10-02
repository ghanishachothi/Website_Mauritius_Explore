from django.contrib import messages
from django.contrib.auth import login, update_session_auth_hash, get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import views as auth_views
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from .forms import CustomPasswordResetForm, ProfileForm, SignUpForm, UserUpdateForm
from .models import Profile


def signup(request):
    """Create Account page."""
    if request.user.is_authenticated:
        return redirect('users:profile')
        
    form = SignUpForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        
        # Log user in
        login(request, user, backend='django.contrib.auth.backends.ModelBackend')
        
        display_name = user.first_name if user.first_name else user.username
        messages.success(request, f'Welcome to Mauritius Explore, {display_name}!')
        return redirect('users:profile')
        
    return render(request, 'users/signup.html', {'form': form})


@login_required
def profile(request):
    """Profile page (view + edit). Full access for standard users and admins."""
    profile_obj, _ = Profile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        user = request.user
        
        # Save User model fields
        full_name = request.POST.get('full_name', '').strip()
        if full_name:
            name_parts = full_name.split(' ', 1)
            user.first_name = name_parts[0]
            user.last_name = name_parts[1] if len(name_parts) > 1 else ''
            
        user.username = request.POST.get('username', user.username)
        user.email = request.POST.get('email', user.email)
        user.save()

        # Check and handle uploaded avatar file
        if 'avatar' in request.FILES:
            profile_obj.avatar = request.FILES['avatar']

        # Save Profile model fields
        profile_obj.gender = request.POST.get('gender', profile_obj.gender)
        profile_obj.language = request.POST.get('language', profile_obj.language)
        profile_obj.phone_number = request.POST.get('phone_number', profile_obj.phone_number)
        profile_obj.nationality = request.POST.get('nationality', profile_obj.nationality)
        profile_obj.reminders = 'reminders' in request.POST
        profile_obj.save()

        messages.success(request, 'Profile updated successfully!')
        return redirect('users:profile')

    return render(request, 'users/profile.html', {
        'profile': profile_obj,
    })


@login_required
def change_password(request):
    """Securely handle user password change."""
    if request.method == 'POST':
        form = PasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            user = form.save()
            # Keeps the user logged in after password change
            update_session_auth_hash(request, user)
            messages.success(request, 'Your password was successfully updated!')
        else:
            for error_list in form.errors.values():
                for error in error_list:
                    messages.error(request, error)

    return redirect('users:profile')


@login_required
def request_delete_account(request):
    """
    Handle account deletion:
    - If user is Admin/Staff: Instantly deletes the account.
    - If user is Regular User: Sets deletion_requested flag for admin approval.
    """
    if request.method == 'POST':
        user = request.user
        
        # Full access override for Admin/Staff
        if user.is_staff or user.is_superuser:
            user.delete()
            messages.success(request, 'Account successfully deleted by admin.')
            return redirect('users:signup')
        
        # Standard workflow for regular users
        profile_obj, _ = Profile.objects.get_or_create(user=user)
        profile_obj.deletion_requested = True
        profile_obj.save()
        messages.info(request, 'Your account deletion request has been submitted to an administrator for approval.')
    
    return redirect('users:profile')


class DevPasswordResetView(auth_views.PasswordResetView):
    """
    Development Password Reset View: Bypasses email sending and terminal line-wrapping issues
    by redirecting directly to the reset confirmation page upon valid email submission.
    """
    template_name = 'users/password_reset.html'
    form_class = CustomPasswordResetForm

    def form_valid(self, form):
        email = form.cleaned_data["email"]
        user_model = get_user_model()
        associated_users = user_model.objects.filter(email__iexact=email)
        
        if associated_users.exists():
            for user in associated_users:
                uid = urlsafe_base64_encode(force_bytes(user.pk))
                token = default_token_generator.make_token(user)
                return redirect(reverse('users:password_reset_confirm', kwargs={'uidb64': uid, 'token': token}))
        
        return super().form_valid(form)