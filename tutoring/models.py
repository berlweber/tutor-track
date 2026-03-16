from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse

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
    hourly_rate = models.IntegerField('תשלום לשעה')
    sponsor = models.CharField('מממן', max_length=1, choices=SPONSORS, default=SPONSORS[0][0])
    start_time = models.TimeField('זמן התחלת הלימוד היומי')
    end_time = models.TimeField('זמן סיום')

    def __str__(self):
        return f"{self.tutor} לומד עם {self.student}"
    
    def get_absolute_url(self):
        return reverse("assignment-detail", kwargs={"pk": self.pk})
    
class Session(models.Model):
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE)
    date = models.DateTimeField()
    time_started = models.TimeField()
    duration = models.DurationField()
    created_at = models.DateTimeField(auto_now_add=True)
    note = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"{self.duration} on {self.date} at {self.time_started}"

    def get_absolute_url(self):
        return reverse("assignment-detail", kwargs={"pk": self.pk})
    
    class Meta:
        ordering = ['-date']
