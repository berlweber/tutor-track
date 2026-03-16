from django import forms
from .models import Session

class SessionForm(forms.ModelForm):
    class Meta:
        model = Session
        fields = ['date', 'time_started', 'duration', 'note']
        labels = {
            'date': 'תאריך',
            'time_started': 'זמן התחלה',
            'duration': 'משך זמן הלימוד',
            'note': 'הערה'
        }

        widgets = {
            'date': forms.DateInput(
                format=('%Y-%m-%d'),
                attrs = {
                    'type': 'date',
                    'placeholder': 'תבחר תאריך'
                }
            )
        }
