import datetime
from decimal import Decimal, ROUND_HALF_UP
from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
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
    BILLING_PER_SESSION = "session"
    BILLING_PER_MONTH = "month"
    BILLING_CHOICES = (
        (BILLING_PER_SESSION, "לפי שיעור"),
        (BILLING_PER_MONTH, "לפי חודש"),
    )

    student = models.ForeignKey(Student, on_delete=models.CASCADE, verbose_name = "בחור")
    tutor = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name = "אברך")
    goal = models.TextField('מטרת הלימוד')
    billing_mode = models.CharField(
        "צורת חיוב",
        max_length=20,
        choices=BILLING_CHOICES,
        default=BILLING_PER_SESSION,
    )
    session_rate = models.DecimalField('תשלום לשיעור', max_digits=10, decimal_places=2)
    monthly_rate = models.DecimalField(
        "תשלום חודשי",
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
    )
    sessions_per_week = models.PositiveIntegerField(
        "מספר מפגשים בשבוע",
        null=True,
        blank=True,
    )
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

    @property
    def is_monthly_billing(self):
        return self.billing_mode == self.BILLING_PER_MONTH

    @property
    def is_session_billing(self):
        return self.billing_mode == self.BILLING_PER_SESSION

    @property
    def expected_sessions_per_month(self):
        if not self.sessions_per_week:
            return Decimal("0")
        return Decimal(str(self.sessions_per_week)) * Decimal("4.3")

    def calculate_monthly_session_rate(self):
        if not self.monthly_rate or not self.sessions_per_week:
            return Decimal("0.00")

        return (
            Decimal(self.monthly_rate) / self.expected_sessions_per_month
        ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    def clean(self):
        super().clean()

        if self.billing_mode == self.BILLING_PER_MONTH:
            if self.monthly_rate in (None, ""):
                raise ValidationError({"monthly_rate": "נא למלא תשלום חודשי."})
            if not self.sessions_per_week:
                raise ValidationError({"sessions_per_week": "נא למלא מספר מפגשים בשבוע."})
            if self.sessions_per_week <= 0:
                raise ValidationError({"sessions_per_week": "מספר מפגשים בשבוע חייב להיות גדול מאפס."})
        else:
            if self.session_rate in (None, ""):
                raise ValidationError({"session_rate": "נא למלא תשלום לשיעור."})

    def save(self, *args, **kwargs):
        if self.billing_mode == self.BILLING_PER_MONTH:
            self.session_rate = self.calculate_monthly_session_rate()
        else:
            self.monthly_rate = None
            self.sessions_per_week = None
        super().save(*args, **kwargs)

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


class AttendanceAdjustment(models.Model):
    TYPE_LATE = "late"
    TYPE_ABSENT = "absent"
    ADJUSTMENT_TYPES = (
        (TYPE_LATE, "איחור"),
        (TYPE_ABSENT, "חיסור"),
    )

    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE)
    date = models.DateField("תאריך")
    adjustment_type = models.CharField("סוג", max_length=12, choices=ADJUSTMENT_TYPES)
    duration = models.DurationField("משך האיחור", null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.get_adjustment_type_display()} on {self.date}"

    def get_absolute_url(self):
        return reverse("assignment-detail", kwargs={"pk": self.assignment_id})

    @property
    def duration_hhmm(self):
        return format_duration_hhmm(self.duration)

    @property
    def deduction_amount(self):
        if self.adjustment_type == self.TYPE_ABSENT:
            return self.assignment.session_rate

        session_length_seconds = (
            self.assignment.session_length.total_seconds()
            if self.assignment.session_length
            else 0
        )
        if not self.duration or session_length_seconds <= 0:
            return Decimal("0.00")

        late_ratio = Decimal(str(self.duration.total_seconds())) / Decimal(str(session_length_seconds))
        return (self.assignment.session_rate * late_ratio).quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP,
        )

    def clean(self):
        super().clean()

        if self.adjustment_type == self.TYPE_LATE:
            if not self.duration:
                raise ValidationError({"duration": "נא למלא את משך האיחור."})
            if self.assignment_id and self.assignment and self.assignment.session_length and self.duration > self.assignment.session_length:
                raise ValidationError({"duration": "משך האיחור לא יכול להיות יותר מאורך השיעור."})
        else:
            self.duration = None

    class Meta:
        ordering = ["-date", "-created_at"]


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
