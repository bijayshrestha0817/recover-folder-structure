from rest_framework import serializers

from student_management.models import Student


class StudentSerializer(serializers.ModelSerializer):
    course_name = serializers.CharField(source="course.name", read_only=True)

    class Meta:
        model = Student
        fields = ["id", "name", "email", "age", "course", "course_name"]

        ordering_fields = ["name", "email", "age", "course__name"]
