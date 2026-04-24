from rest_framework import status

from student_management.custom.custom_api_exception import CustomException
from student_management.models import Student
from student_management.repository.student_repository import StudentRepository


class StudentService:
    def list_students(self):
        repo = StudentRepository()
        student = repo.get_all_students()
        if not student.exists():
            raise CustomException(message="No Student Found", status_code=status.HTTP_404_NOT_FOUND)
        return student

    def create_student(self, validated_data):
        repo = StudentRepository()
        if Student.objects.filter(email=validated_data["email"]):
            raise CustomException(
                message="Student with this email already exits",
                status_code=status.HTTP_409_CONFLICT,
            )
        return repo.create_student(validated_data)

    def update_student(self, student, validated_data):
        repo = StudentRepository()
        if (
            "email" in validated_data
            and Student.objects.filter(email=validated_data["email"])
            .exclude(id=student.id)
            .exists()
        ):
            raise CustomException(
                message="Student with this email already exists",
                status_code=status.HTTP_409_CONFLICT,
            )
        return repo.update_student(student, validated_data)

    def delete_student(self, student):
        repo = StudentRepository()
        return repo.delete_student(student)
