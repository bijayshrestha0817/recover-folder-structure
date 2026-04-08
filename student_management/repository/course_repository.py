from student_management.models import Course


class CourseRepository:
    def get_all_courses():
        return Course.objects.all()
    
    def create_course(data):
        return Course.objects.create(**data)