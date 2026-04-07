from dataclasses import field

from rest_framework import serializers

from student_management.models import Student

class StudentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Student
        fields = "__all__"