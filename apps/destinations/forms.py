from django import forms

from .models import Suggestion


class SuggestionForm(forms.ModelForm):
    """"Suggest an idea" pop-up on Explore the Island."""

    class Meta:
        model = Suggestion
        fields = ['name', 'email', 'region', 'idea']
