import re

from django import forms

from .models import Booking, Payment


class ReserveForm(forms.ModelForm):
    """Reserve Your Experience form."""

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


class CheckoutForm(forms.Form):
    """Secure Checkout form (demo - nothing is really charged)."""
    method = forms.ChoiceField(choices=Payment.Method.choices, widget=forms.RadioSelect,
                               initial=Payment.Method.CARD)
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
