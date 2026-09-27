from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Profile


class SignUpForm(forms.Form):
    full_name = forms.CharField(max_length=300, required=True)
    email = forms.EmailField(required=True)
    gender = forms.CharField(max_length=20, required=False)
    language = forms.CharField(max_length=100, required=False)
    phone_number = forms.CharField(max_length=20, required=False)
    nationality = forms.CharField(max_length=100, required=False)
    password1 = forms.CharField(widget=forms.PasswordInput, required=True)
    password2 = forms.CharField(widget=forms.PasswordInput, required=True)

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("An account with this email already exists.")
        return email

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get("password1")
        p2 = cleaned_data.get("password2")
        if p1 and p2 and p1 != p2:
            self.add_error('password2', "Passwords do not match.")
        return cleaned_data

    def save(self):
        cd = self.cleaned_data
        email = cd['email']
        
        # 1. Split full name
        full_name = cd.get('full_name', '').strip()
        name_parts = full_name.split(' ', 1) if full_name else ['', '']
        first_name = name_parts[0]
        last_name = name_parts[1] if len(name_parts) > 1 else ''

        # 2. Create User
        user = User.objects.create_user(
            username=email,
            email=email,
            password=cd['password1'],
            first_name=first_name,
            last_name=last_name
        )

        # 3. Create or update Profile and force-save all fields
        profile, _ = Profile.objects.get_or_create(user=user)
        profile.gender = cd.get('gender', '')
        profile.language = cd.get('language', '')
        profile.phone_number = cd.get('phone_number', '')
        profile.nationality = cd.get('nationality', '')
        profile.save()

        return user


class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'username', 'email']


class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['gender', 'language', 'phone_number', 'nationality', 'reminders', 'avatar', 'bio']
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 3}),
        }