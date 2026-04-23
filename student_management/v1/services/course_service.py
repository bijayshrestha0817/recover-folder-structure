from rest_framework import status

from student_management.custom.custom_api_exception import CustomException
from student_management.models import Course
from student_management.repository.course_repository import CourseRepository


class CourseService:
    def list_course(self):
        repo = CourseRepository()
        course = repo.get_all_courses()
        if not course():
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
