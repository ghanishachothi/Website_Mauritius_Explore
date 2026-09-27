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
                               initial=Payment.Method.JUICE)
    card_number = forms.CharField(required=False, max_length=23)

    def clean(self):
        data = super().clean()
        if data.get('method') == Payment.Method.CARD:
            data['card_number'] = re.sub(r'\D', '', data.get('card_number', '')) or '0000'
        return data