from student_management.models import Student


class StudentRepository:
    def get_all_students(self):
        return Student.objects.select_related("course").all()

    def create_student(self, data):
        return Student.objects.create(**data)

    def update_student(self, student, data):
        for key, value in data.items():
            setattr(student, key, value)
        student.save()
        return student

    def delete_student(self, student):
        student.delete()
