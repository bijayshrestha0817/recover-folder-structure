from student_management.repository.course_repository import CourseRepository


class CourseService:
    def list_course(self):
        repo = CourseRepository()
        return repo.get_all_courses()

    def create_course(self, validated_data):
        repo = CourseRepository()
        return repo.create_course(validated_data)
