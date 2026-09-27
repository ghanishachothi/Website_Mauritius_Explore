from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

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
    """Profile page (view + edit)."""
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

        # Save Profile model fields
        profile_obj.gender = request.POST.get('gender', '')
        profile_obj.language = request.POST.get('language', '')
        profile_obj.phone_number = request.POST.get('phone_number', '')
        profile_obj.nationality = request.POST.get('nationality', '')
        profile_obj.reminders = 'reminders' in request.POST
        profile_obj.save()

        messages.success(request, 'Profile updated successfully!')
        return redirect('users:profile')

    return render(request, 'users/profile.html', {
        'profile': profile_obj,
    })