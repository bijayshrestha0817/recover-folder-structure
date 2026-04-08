from student_management.repository.student_repository import StudentRepository


class StudentService:
    def list_students(self):
        repo = StudentRepository()
        return repo.get_all_students()

    def create_student(self, validated_data):
        repo = StudentRepository()
        return repo.create_student(validated_data)
