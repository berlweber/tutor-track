from dataclasses import field

from django import forms
from .models import Session

class SessionForm(forms.ModelForm):
    class Meta:
        model = Session
        fields = ['date', 'time_started', 'duration', 'note']

        widgets = {
            'date': forms.DateInput(
                format=('%Y-%m-%d'),
                attrs = {
                    'type': 'date',
                    'placeholder': 'Select a date'
                }
            )
        }
