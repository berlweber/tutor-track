import datetime

from django import forms
from django.contrib.auth.forms import AuthenticationForm

from .models import (
    Assignment,
    AttendanceAdjustment,
    MonthlyReport,
    Session,
    Student,
    format_user_display,
)


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
        self.fields["billing_mode"].widget = forms.RadioSelect(
            choices=self.fields["billing_mode"].choices
        )
        self.fields["session_rate"].required = False
        self.fields["monthly_rate"].required = False
        self.fields["sessions_per_week"].required = False
        for field_name, field in self.fields.items():
            if field.required:
                if isinstance(field, forms.ModelChoiceField):
                    field.error_messages["required"] = "נא לבחור ערך מהרשימה."
                else:
                    field.error_messages["required"] = "נא למלא שדה זה."

        self.fields["start_time"].error_messages["invalid"] = "נא להזין שעה בפורמט 24 שעות, לדוגמה 18:30."
        self.fields["end_time"].error_messages["invalid"] = "נא להזין שעה בפורמט 24 שעות, לדוגמה 19:15."
        self.fields["session_rate"].widget.attrs.update({"min": "0", "step": "0.01"})
        self.fields["monthly_rate"].widget.attrs.update({"min": "0", "step": "0.01"})
        self.fields["sessions_per_week"].widget.attrs.update({"min": "1", "step": "1"})

    class Meta:
        model = Assignment
        exclude = ["session_length"]
        widgets = {
            "session_rate": forms.NumberInput(),
            "monthly_rate": forms.NumberInput(),
            "sessions_per_week": forms.NumberInput(),
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

    def clean(self):
        cleaned_data = super().clean()
        billing_mode = cleaned_data.get("billing_mode")
        session_rate = cleaned_data.get("session_rate")
        monthly_rate = cleaned_data.get("monthly_rate")
        sessions_per_week = cleaned_data.get("sessions_per_week")

        if billing_mode == Assignment.BILLING_PER_MONTH:
            if monthly_rate is None:
                self.add_error("monthly_rate", "נא למלא תשלום חודשי.")
            if not sessions_per_week:
                self.add_error("sessions_per_week", "נא למלא מספר מפגשים בשבוע.")
        elif session_rate is None:
            self.add_error("session_rate", "נא למלא תשלום לשיעור.")

        return cleaned_data


class SessionForm(forms.ModelForm):
    duration = HHMMDurationField(
        label="משך זמן הלימוד",
        required=True,
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
            "note": forms.Textarea(attrs={"rows": 3, "class": "session-note"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["date"].input_formats = ["%d/%m/%Y", "%Y-%m-%d"]
        self.fields["date"].error_messages["required"] = "נא לבחור תאריך."
        self.fields["date"].error_messages["invalid"] = "נא להזין תאריך בפורמט יום/חודש/שנה."
        self.fields["duration"].error_messages["required"] = "נא להזין משך שיעור."


class AttendanceAdjustmentForm(forms.ModelForm):
    duration = HHMMDurationField(
        label="משך האיחור",
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
            "invalid": "נא להזין משך בפורמט שעות:דקות, לדוגמה 00:15.",
        },
    )

    class Meta:
        model = AttendanceAdjustment
        fields = ["date", "adjustment_type", "duration"]
        labels = {
            "date": "תאריך",
            "adjustment_type": "סוג דיווח",
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

    def clean(self):
        cleaned_data = super().clean()
        adjustment_type = cleaned_data.get("adjustment_type")
        duration = cleaned_data.get("duration")

        if adjustment_type == AttendanceAdjustment.TYPE_LATE and not duration:
            self.add_error("duration", "נא למלא את משך האיחור.")
        elif adjustment_type == AttendanceAdjustment.TYPE_ABSENT:
            cleaned_data["duration"] = None
        return cleaned_data


class MonthPickerForm(forms.Form):
    month = forms.DateField(
        label="חודש",
        widget=forms.DateInput(
            format="%Y-%m",
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
        fields = ["report_date", "content"]
        labels = {
            "report_date": "תאריך העדכון",
            "content": "עידכון התקדמות",
        }
        widgets = {
            "report_date": forms.DateInput(
                format="%d/%m/%Y",
                attrs={
                    "lang": "he-IL",
                    "class": "js-he-date",
                    "autocomplete": "off",
                    "placeholder": "יום/חודש/שנה",
                    "data-picker-type": "date",
                }
            ),
            "content": forms.Textarea(
                attrs={
                    "placeholder": "כתיבת סיכום ההתקדמות, נקודות לחיזוק ויעדים להמשך.",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["report_date"].input_formats = ["%d/%m/%Y", "%Y-%m-%d"]
        self.fields["report_date"].error_messages["required"] = "נא לבחור תאריך."
        self.fields["report_date"].error_messages["invalid"] = "נא להזין תאריך בפורמט יום/חודש/שנה."
        self.fields["content"].error_messages["required"] = "נא לכתוב עידכון התקדמות."


class StudentForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = ["first_name", "last_name"]
        labels = {
            "first_name": "שם פרטי",
            "last_name": "שם משפחה",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["first_name"].required = True
        self.fields["last_name"].required = True
        self.fields["first_name"].error_messages["required"] = "נא למלא שם פרטי."
        self.fields["last_name"].error_messages["required"] = "נא למלא שם משפחה."


class LoginForm(AuthenticationForm):
    error_messages = {
        "invalid_login": "שם המשתמש או הסיסמה אינם נכונים.",
        "inactive": "החשבון הזה אינו פעיל.",
    }

    username = forms.CharField(label="שם משתמש")
    password = forms.CharField(label="סיסמה", widget=forms.PasswordInput)
