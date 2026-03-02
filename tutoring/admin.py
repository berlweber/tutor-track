from django.contrib import admin

from .models import Session, Student, Assignment

# Register your models here.
admin.site.register(Student)
admin.site.register(Assignment)
admin.site.register(Session)
