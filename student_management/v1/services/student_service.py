from student_management.repository.student_repository import StudentRepository


class StudentService:
    def list_students():
        return StudentRepository.get_all_students()
    
    def create_student(validated_data):
        return StudentRepository.create_student(validated_data)