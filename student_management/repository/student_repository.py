from student_management.models import Student


class StudentRepository:
    def get_all_students(self):
        return Student.objects.select_related("course").all()

    def create_student(self, data):
        return Student.objects.create(**data)
