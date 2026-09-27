from django.contrib import messages
from django.contrib.auth import login, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404, redirect, render

from .forms import ProfileForm, SignUpForm, UserUpdateForm
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