from django import forms
from .models import Review


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