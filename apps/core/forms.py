from django import forms

from .models import ContactMessage


class ContactForm(forms.ModelForm):
    """Help & Contact pop-up (in base.html)."""

    class Meta:
        model = ContactMessage
        fields = ['name', 'email', 'topic', 'message']


class WaitlistForm(forms.Form):
    """"Tell me when it's in the store" (app panel in base.html)."""
    email = forms.EmailField()
    store = forms.CharField(max_length=10, required=False)