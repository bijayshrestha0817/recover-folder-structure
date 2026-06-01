from student_management.core.service import BaseService
from student_management.repository.student_repository import StudentRepository


class StudentService(BaseService):
    repository_class = StudentRepository
    entity_name = "Student"
    unique_field = "email"
