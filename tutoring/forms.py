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
            ),
            'time_started': forms.TimeInput(
                attrs = {
                    'type': 'time',
                }
            ),
            'duration': forms.TimeInput(
                attrs = {
                    'type': 'time',
                    'placeholder': '00:00'
                }
            )
        }
    
class MonthPickerForm(forms.Form):
    
    month = forms.DateField(
        widget=forms.DateInput(attrs={"type": "month"}),
        input_formats=["%Y-%m"],  
    )
        
