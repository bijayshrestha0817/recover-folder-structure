from django.db import models

from student_management.core.models import AuditModel

# Create your models here.


class Course(AuditModel):
    name = models.CharField(max_length=50)

    class Meta:
        ordering = ["-id"]

    def __str__(self):
        return self.name


class Student(AuditModel):
    name = models.CharField(max_length=50)
    age = models.IntegerField()
    email = models.EmailField(unique=True, db_index=True)

    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="students")

    class Meta:
        ordering = ["-id"]

    def __str__(self):
        return f"{self.name} ({self.email})"
