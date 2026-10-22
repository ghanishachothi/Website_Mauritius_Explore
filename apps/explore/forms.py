from django import forms
from .models import ContactMessage
import re
from django.contrib.auth.forms import UserCreationForm, PasswordResetForm, SetPasswordForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from .models import Profile
from .models import Suggestion
from .models import Review
from datetime import date, timedelta
from .models import Booking, Payment
from django.utils import timezone


# ======================================================================
# from the old "core" app
# ======================================================================

class ContactForm(forms.ModelForm):
    """Help & Contact pop-up (in base.html)."""

    class Meta:
        model = ContactMessage
        fields = ['name', 'email', 'topic', 'message']


class WaitlistForm(forms.Form):
    """"Tell me when it's in the store" (app panel in base.html)."""
    email = forms.EmailField()
    store = forms.CharField(max_length=10, required=False)


# ======================================================================
# from the old "users" app
# ======================================================================

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


# ======================================================================
# from the old "destinations" app
# ======================================================================

class SuggestionForm(forms.ModelForm):
    """"Suggest an idea" pop-up on Explore the Island."""

    class Meta:
        model = Suggestion
        fields = ['name', 'email', 'region', 'idea']


# ======================================================================
# from the old "experiences" app
# ======================================================================

class ReviewForm(forms.ModelForm):
    rating = forms.IntegerField(
        min_value=1,
        max_value=5,
        widget=forms.RadioSelect(choices=[(i, i) for i in range(1, 6)]),
    )

    class Meta:
        model = Review
        fields = ['event', 'rating', 'comment']
        widgets = {
            'event': forms.Select(attrs={'id': 'reviewPlace'}),
            'comment': forms.Textarea(
                attrs={
                    'id': 'reviewText',
                    'rows': 4,
                    'placeholder': 'Tell other travellers about your experience...',
                }
            ),
        }

    def clean_rating(self):
        rating = self.cleaned_data.get('rating')
        if not rating or rating < 1 or rating > 5:
            raise forms.ValidationError('Please select a valid star rating between 1 and 5.')
        return rating


# ======================================================================
# from the old "bookings" app
# ======================================================================

class ReserveForm(forms.ModelForm):
    """Reserve Your Experience form (for Events)."""

    class Meta:
        model = Booking
        fields = ['number_of_people', 'full_name', 'email', 'phone', 'special_requests']
        widgets = {'special_requests': forms.Textarea(attrs={'rows': 3})}

    def __init__(self, *args, event=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.event = event

    def clean_number_of_people(self):
        n = self.cleaned_data['number_of_people']
        if n < 1:
            raise forms.ValidationError('At least 1 person.')
        if self.event and n > self.event.spots_left:
            raise forms.ValidationError(f'Only {self.event.spots_left} spots left.')
        return n




class ReservePackageForm(forms.ModelForm):
    """Reserve Your Experience form (for Packages) — the "Reserve Package" button
    on Guides & Packages and Guide Profile pages leads here."""

    preferred_time = forms.TimeField(
        required=True, label='Preferred Time',
        widget=forms.TimeInput(attrs={'type': 'time', 'class': 'rx-input'}),
        error_messages={'required': 'Please choose a preferred time.', 'invalid': 'Enter a valid time.'},
    )

    agree = forms.BooleanField(
        required=True,
        error_messages={'required': 'Please agree to the Terms & Conditions and Privacy Policy.'},
    )

    class Meta:
        model = Booking
        fields = ['preferred_date', 'alternative_date', 'number_of_people', 'guide',
                  'full_name', 'email', 'phone', 'special_requests']
        widgets = {
            'preferred_date': forms.DateInput(attrs={'type': 'date', 'class': 'rx-input'}),
            'alternative_date': forms.DateInput(attrs={'type': 'date', 'class': 'rx-input'}),
            'number_of_people': forms.NumberInput(attrs={'class': 'rx-input', 'min': 1}),
            'guide': forms.Select(attrs={'class': 'rx-input rx-select'}),
            'full_name': forms.TextInput(attrs={'class': 'rx-input'}),
            'email': forms.EmailInput(attrs={'class': 'rx-input'}),
            'phone': forms.TextInput(attrs={'class': 'rx-input'}),
            'special_requests': forms.Textarea(attrs={'rows': 3, 'class': 'rx-textarea',
                'placeholder': 'Any special request or requirements? (e.g. dietary needs, accessibility, interests)'}),
        }

    def __init__(self, *args, package=None, for_item=False, **kwargs):
        super().__init__(*args, **kwargs)
        self.package = package
        if package is not None:
            choices = package.guide_choices
            self.fields['guide'].queryset = type(package.guide).objects.filter(
                pk__in=[g.pk for g in choices]
            )
            if not self.initial.get('guide') and package.guide:
                self.initial['guide'] = package.guide.pk
        self.fields['guide'].required = not for_item
        self.fields['preferred_date'].required = True

    def clean_preferred_time(self):
        from datetime import time as _time
        t = self.cleaned_data['preferred_time']
        lo = getattr(self, 'time_min', None) or _time(6, 0)
        hi = getattr(self, 'time_max', None) or _time(22, 0)
        if t < lo or t > hi:
            raise forms.ValidationError('Please choose a time between %s and %s.' % (lo.strftime('%H:%M'), hi.strftime('%H:%M')))
        return t

    @staticmethod
    def earliest_date():
        """Bookings start from tomorrow."""
        return date.today() + timedelta(days=1)

    def clean_preferred_date(self):
        day = self.cleaned_data['preferred_date']
        if day < self.earliest_date():
            raise forms.ValidationError('Please choose a date from tomorrow onwards.')
        return day

    def clean_alternative_date(self):
        day = self.cleaned_data.get('alternative_date')
        if day and day < self.earliest_date():
            raise forms.ValidationError('Please choose a date from tomorrow onwards.')
        return day

    def clean(self):
        cleaned = super().clean()
        preferred = cleaned.get('preferred_date')
        alternative = cleaned.get('alternative_date')
        if preferred and alternative and alternative < preferred:
            self.add_error('alternative_date',
                            "The alternative date can't be earlier than the preferred date.")
        return cleaned

    def clean_number_of_people(self):
        n = self.cleaned_data['number_of_people']
        if n < 1:
            raise forms.ValidationError('At least 1 person.')
        max_people = getattr(self.package, 'max_people', None)
        if self.package and max_people and n > max_people:
            raise forms.ValidationError(f'This package allows a maximum of {max_people} people.')
        return n


class CheckoutForm(forms.Form):
    """Secure Checkout form (demo - nothing is really charged)."""
    full_name = forms.CharField(max_length=150, widget=forms.TextInput(attrs={'class': 'input'}))
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'input'}))
    phone = forms.CharField(max_length=30, required=False, widget=forms.TextInput(attrs={'class': 'input'}))
    method = forms.ChoiceField(choices=Payment.Method.choices, widget=forms.RadioSelect,
                               initial=Payment.Method.JUICE)
    cardholder_name = forms.CharField(required=False)
    card_number = forms.CharField(required=False, max_length=23)
    expiry = forms.CharField(required=False, max_length=5, help_text='MM/YY')
    cvv = forms.CharField(required=False, max_length=4, widget=forms.PasswordInput)



    def __init__(self, *args, booking=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.booking = booking

    def clean(self):
        data = super().clean()
        b = self.booking
        if b is not None:
            def _n(s):
                return ' '.join((s or '').lower().split())
            def _p(s):
                d = re.sub(r'\D', '', s or '')
                if d.startswith('230') and len(d) > 8:
                    d = d[3:]
                return d.lstrip('0')
            msg = 'This does not match the details you gave when you reserved.'
            if data.get('full_name') is not None and _n(data['full_name']) != _n(b.full_name):
                self.add_error('full_name', msg)
            if data.get('email') is not None and (data['email'] or '').strip().lower() != (b.email or '').strip().lower():
                self.add_error('email', msg)
            if 'phone' in data and _p(data.get('phone')) != _p(b.phone):
                self.add_error('phone', msg)
        if data.get('method') == Payment.Method.CARD:
            number = re.sub(r'\D', '', data.get('card_number', ''))
            if not data.get('cardholder_name'):
                self.add_error('cardholder_name', 'Required for card payments.')
            if not 13 <= len(number) <= 19:
                self.add_error('card_number', 'Enter a valid card number.')
            if not re.fullmatch(r'(0[1-9]|1[0-2])/\d{2}', data.get('expiry', '')):
                self.add_error('expiry', 'Use MM/YY.')
            if not re.fullmatch(r'\d{3,4}', data.get('cvv', '')):
                self.add_error('cvv', 'Enter a valid CVV.')
            data['card_number'] = number
        return data