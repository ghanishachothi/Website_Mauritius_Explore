import re
from django import forms
from django.contrib.auth.forms import UserCreationForm, PasswordResetForm, SetPasswordForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from .models import Profile


class CustomPasswordResetForm(PasswordResetForm):
    """Custom form to style the email field on the password reset page."""
    email = forms.EmailField(
        max_length=254,
        widget=forms.EmailInput(attrs={
            'placeholder': 'Enter your email address',
            'autocomplete': 'email',
            'class': 'form-control',
        })
    )


class CustomSetPasswordForm(SetPasswordForm):
    """Custom form to style the new password fields and enforce complexity rules on password reset confirm page."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})

    def clean_new_password1(self):
        password = self.cleaned_data.get('new_password1')

        if not password:
            return password

        # 1. At least 8 characters
        if len(password) < 8:
            raise ValidationError("Password must be at least 8 characters long.")
        
        # 2. At least 1 uppercase letter
        if not re.search(r'[A-Z]', password):
            raise ValidationError("Password must contain at least one uppercase letter (A-Z).")
        
        # 3. At least 1 digit
        if not re.search(r'\d', password):
            raise ValidationError("Password must contain at least one digit (0-9).")
        
        # 4. At least 1 symbol
        if not re.search(r'[^a-zA-Z0-9]', password):
            raise ValidationError("Password must contain at least one symbol (e.g., !@#$%^&*).")

        return password


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

        # Use full_name as the username (fall back to email if blank)
        username = full_name if full_name else email

        # 2. Create User
        user = User.objects.create_user(
            username=username,
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
        fields = ['gender', 'language', 'phone_number', 'nationality', 'avatar', 'bio']
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 3}),
        }