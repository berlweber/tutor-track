import datetime
from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse


def format_duration_hhmm(value):
    if not isinstance(value, datetime.timedelta):
        return ""

    total_seconds = int(value.total_seconds())
    hours, remainder = divmod(total_seconds, 3600)
    minutes = remainder // 60
    return f"{hours:02d}:{minutes:02d}"


def format_user_display(user):
    if user and user.last_name:
        return f"הרב {user.last_name}"
    if user:
        return user.username
    return ""


HEBREW_MONTHS = (
    "",
    "ינואר",
    "פברואר",
    "מרץ",
    "אפריל",
    "מאי",
    "יוני",
    "יולי",
    "אוגוסט",
    "ספטמבר",
    "אוקטובר",
    "נובמבר",
    "דצמבר",
)


def month_label(date_value):
    if not date_value:
        return ""
    return f"{HEBREW_MONTHS[date_value.month]} {date_value.year}"

# Create your models here.
class Student(models.Model):
    name = models.CharField('שם התלמיד', max_length=50)

    def get_absolute_url(self):
        return reverse("assignment-create")

    def __str__(self):
        return self.name

SPONSORS = (
    ('P', 'הורים'),
    ('S', 'ישיבה'),
    ('O', 'יגדל/קופה')
)

class Assignment(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, verbose_name = "בחור")
    tutor = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name = "אברך")
    goal = models.TextField('מטרת הלימוד')
    session_rate = models.IntegerField('תשלום לשיעור')
    sponsor = models.CharField('מממן', max_length=1, choices=SPONSORS, default=SPONSORS[0][0])
    start_time = models.TimeField('זמן התחלת הלימוד היומי')
    end_time = models.TimeField('זמן סיום')
    session_length = models.DurationField('אורך שיעור')

    def __str__(self):
        return f"{self.tutor_display_name} לומד עם {self.student}"
    
    def get_absolute_url(self):
        return reverse("assignment-detail", kwargs={"pk": self.pk})

    @property
    def session_length_hhmm(self):
        return format_duration_hhmm(self.session_length)

    @property
    def tutor_display_name(self):
        return format_user_display(self.tutor)
    
class Session(models.Model):
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE)
    date = models.DateField()
    time_started = models.TimeField(null=True, blank=True)
    duration = models.DurationField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    note = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"{self.duration} on {self.date} at {self.time_started}"

    def get_absolute_url(self):
        return reverse("assignment-detail", kwargs={"pk": self.pk})

    @property
    def duration_hhmm(self):
        return format_duration_hhmm(self.duration)
    
    class Meta:
        ordering = ['-date']


class MonthlyReport(models.Model):
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE)
    month = models.DateField("חודש הדוח")
    content = models.TextField("דוח התקדמות")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if self.month:
            self.month = self.month.replace(day=1)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"דוח {month_label(self.month)} עבור {self.assignment.student}"

    def get_absolute_url(self):
        return reverse("assignment-detail", kwargs={"pk": self.assignment_id})

    @property
    def month_display(self):
        return month_label(self.month)

    class Meta:
        ordering = ["-month", "-updated_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["assignment", "month"],
                name="unique_monthly_report_per_assignment",
            )
        ]
