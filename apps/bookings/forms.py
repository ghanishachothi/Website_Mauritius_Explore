import re
from datetime import date, timedelta
 
from django import forms
 
from .models import Booking, Payment

from django.utils import timezone
 
 
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
 
    def __init__(self, *args, package=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.package = package
        if package is not None:
            choices = package.guide_choices
            self.fields['guide'].queryset = type(package.guide).objects.filter(
                pk__in=[g.pk for g in choices]
            )
            if not self.initial.get('guide') and package.guide:
                self.initial['guide'] = package.guide.pk
        self.fields['guide'].required = True
        self.fields['preferred_date'].required = True
 
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


 
    def clean(self):
        data = super().clean()
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
 
