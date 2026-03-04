from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse

# Create your models here.
class Student(models.Model):
    name = models.CharField(max_length=50)

    def get_absolute_url(self):
        return reverse("assignment-create")

    def __str__(self):
        return self.name
SPONSORS = (
    ('P', 'Parent'),
    ('S', 'School'),
    ('O', 'Other fund')
)

class Assignment(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    tutor = models.ForeignKey(User, on_delete=models.CASCADE)
    goal = models.TextField()
    hourly_rate = models.IntegerField()
    sponsor = models.CharField(max_length=1, choices=SPONSORS, default=SPONSORS[0][0])
    start_time = models.TimeField()
    end_time = models.TimeField()

    def __str__(self):
        return f"{self.tutor} tutoring {self.student}"
    
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
