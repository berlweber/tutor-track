from django.contrib import admin

from .models import Assignment, AttendanceAdjustment, Session, Student

# Register your models here.
admin.site.register(Student)
admin.site.register(Assignment)
admin.site.register(Session)
admin.site.register(AttendanceAdjustment)
