import datetime

from django import forms
from django.contrib.auth.forms import AuthenticationForm

from .models import Assignment, MonthlyReport, Session, format_user_display


class HHMMDurationField(forms.DurationField):
    def prepare_value(self, value):
        if isinstance(value, datetime.timedelta):
            total_seconds = int(value.total_seconds())
            hours, remainder = divmod(total_seconds, 3600)
            minutes = remainder // 60
            return f"{hours:02d}:{minutes:02d}"
        return super().prepare_value(value)

    def to_python(self, value):
        if isinstance(value, str) and value:
            parts = value.split(":")
            if len(parts) == 2:
                hours, minutes = parts
                try:
                    return datetime.timedelta(hours=int(hours), minutes=int(minutes))
                except ValueError:
                    pass
        return super().to_python(value)


class AssignmentForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["tutor"].label_from_instance = format_user_display
        self.fields["start_time"].input_formats = ["%H:%M"]
        self.fields["end_time"].input_formats = ["%H:%M"]
        for field_name, field in self.fields.items():
            if field.required:
                if isinstance(field, forms.ModelChoiceField):
                    field.error_messages["required"] = "נא לבחור ערך מהרשימה."
                else:
                    field.error_messages["required"] = "נא למלא שדה זה."

        self.fields["start_time"].error_messages["invalid"] = "נא להזין שעה בפורמט 24 שעות, לדוגמה 18:30."
        self.fields["end_time"].error_messages["invalid"] = "נא להזין שעה בפורמט 24 שעות, לדוגמה 19:15."

    class Meta:
        model = Assignment
        exclude = ["session_length"]
        widgets = {
            "start_time": forms.TimeInput(
                format="%H:%M",
                attrs={
                    "placeholder": "שעה:דקה",
                    "inputmode": "numeric",
                    "lang": "he-IL",
                    "class": "js-he-clock-time",
                    "autocomplete": "off",
                    "data-picker-type": "time",
                },
            ),
            "end_time": forms.TimeInput(
                format="%H:%M",
                attrs={
                    "placeholder": "שעה:דקה",
                    "inputmode": "numeric",
                    "lang": "he-IL",
                    "class": "js-he-clock-time",
                    "autocomplete": "off",
                    "data-picker-type": "time",
                },
            ),
        }


class SessionForm(forms.ModelForm):
    duration = HHMMDurationField(
        label="משך זמן הלימוד",
        required=False,
        widget=forms.TextInput(
            attrs={
                "placeholder": "שעות:דקות",
                "inputmode": "numeric",
                "class": "js-he-duration",
                "autocomplete": "off",
                "data-picker-type": "duration",
            }
        ),
        error_messages={
            "invalid": "נא להזין משך בפורמט שעות:דקות, לדוגמה 01:30.",
        }
    )

    class Meta:
        model = Session
        fields = ["date", "duration", "note"]
        labels = {
            "date": "תאריך",
            "duration": "משך זמן הלימוד",
            "note": "הערה",
        }
        widgets = {
            "date": forms.DateInput(
                format="%d/%m/%Y",
                attrs={
                    "placeholder": "יום/חודש/שנה",
                    "inputmode": "numeric",
                    "lang": "he-IL",
                    "class": "js-he-date",
                    "autocomplete": "off",
                    "data-picker-type": "date",
                },
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["date"].input_formats = ["%d/%m/%Y", "%Y-%m-%d"]
        self.fields["date"].error_messages["required"] = "נא לבחור תאריך."
        self.fields["date"].error_messages["invalid"] = "נא להזין תאריך בפורמט יום/חודש/שנה."
        if self.fields["duration"].required:
            self.fields["duration"].error_messages["required"] = "נא להזין משך שיעור."


class MonthPickerForm(forms.Form):
    month = forms.DateField(
        label="חודש",
        widget=forms.DateInput(
            attrs={
                "lang": "he-IL",
                "class": "js-he-month",
                "autocomplete": "off",
                "placeholder": "בחר חודש",
                "data-picker-type": "month",
            }
        ),
        input_formats=["%Y-%m"],
        error_messages={
            "required": "נא לבחור חודש.",
            "invalid": "נא לבחור חודש תקין.",
        },
    )


class MonthlyReportForm(forms.ModelForm):
    class Meta:
        model = MonthlyReport
        fields = ["month", "content"]
        labels = {
            "month": "חודש הדוח",
            "content": "דוח התקדמות",
        }
        widgets = {
            "month": forms.DateInput(
                attrs={
                    "lang": "he-IL",
                    "class": "js-he-month",
                    "autocomplete": "off",
                    "placeholder": "בחר חודש",
                    "data-picker-type": "month",
                }
            ),
            "content": forms.Textarea(
                attrs={
                    "placeholder": "כתיבת סיכום ההתקדמות של החודש, נקודות לחיזוק ויעדים להמשך.",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["month"].input_formats = ["%Y-%m", "%d/%m/%Y"]
        self.fields["month"].error_messages["required"] = "נא לבחור חודש."
        self.fields["month"].error_messages["invalid"] = "נא לבחור חודש תקין."
        self.fields["content"].error_messages["required"] = "נא לכתוב דוח התקדמות."

    def clean_month(self):
        month = self.cleaned_data["month"]
        return month.replace(day=1)


class LoginForm(AuthenticationForm):
    error_messages = {
        "invalid_login": "שם המשתמש או הסיסמה אינם נכונים.",
        "inactive": "החשבון הזה אינו פעיל.",
    }

    username = forms.CharField(label="שם משתמש")
    password = forms.CharField(label="סיסמה", widget=forms.PasswordInput)
