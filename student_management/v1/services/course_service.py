from rest_framework import status

from student_management.custom.custom_api_exception import CustomException
from student_management.models import Course
from student_management.repository.course_repository import CourseRepository


class CourseService:
    def list_course(self):
        repo = CourseRepository()
        course = repo.get_all_courses()
        if not course.exists():
            raise CustomException(message="No Course Found", status_code=status.HTTP_404_NOT_FOUND)
        return course

    def create_course(self, validated_data):
        repo = CourseRepository()
        if Course.objects.filter(name=validated_data["name"]).exists():
            raise CustomException(
                message="Course with this name already exists",
                status_code=status.HTTP_409_CONFLICT,
            )
        return repo.create_course(validated_data)

    def update_course(self, course, validated_data):
        repo = CourseRepository()
        if (
            "name" in validated_data
            and Course.objects.filter(name=validated_data["name"]).exclude(id=course.id).exists()
        ):
            raise CustomException(
                message="Course with this name already exists",
                status_code=status.HTTP_409_CONFLICT,
            )
        return repo.update_course(course, validated_data)

    def delete_course(self, course):
        repo = CourseRepository()
        return repo.delete_course(course)
