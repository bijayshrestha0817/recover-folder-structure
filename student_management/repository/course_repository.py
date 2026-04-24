from student_management.models import Course


class CourseRepository:
    def get_all_courses(self):
        return Course.objects.all()

    def create_course(self, data):
        return Course.objects.create(**data)

    def update_course(self, course, data):
        for key, value in data.items():
            setattr(course, key, value)
        course.save()
        return course

    def delete_course(self, course):
        course.delete()
