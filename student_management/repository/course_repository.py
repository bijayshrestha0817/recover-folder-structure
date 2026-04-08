from student_management.models import Course


class CourseRepository:
    def get_all_courses(self):
        return Course.objects.all()

    def create_course(self, data):
        return Course.objects.create(**data)
