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
        login(request, user)
        messages.success(request, f'Welcome to Mauritius Explore, {user.first_name}!')
        return redirect('users:profile')
    return render(request, 'users/signup.html', {'form': form})


@login_required
def profile(request):
    """Profile page (view + edit)."""
    profile, _ = Profile.objects.get_or_create(user=request.user)
    user_form = UserUpdateForm(request.POST or None, instance=request.user)
    profile_form = ProfileForm(request.POST or None, request.FILES or None, instance=profile)
    if request.method == 'POST' and user_form.is_valid() and profile_form.is_valid():
        user_form.save()
        profile_form.save()
        messages.success(request, 'Profile updated.')
        return redirect('users:profile')
    return render(request, 'users/profile.html', {
        'profile': profile,
        'user_form': user_form,
        'profile_form': profile_form,
    })
