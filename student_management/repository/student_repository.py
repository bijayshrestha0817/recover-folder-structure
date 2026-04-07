
from student_management.models import Student


class StudentRepository:
    def get_all_students():
        return Student.objects.all()
    
    def create_student(data):
        return Student.objects.create(**data)