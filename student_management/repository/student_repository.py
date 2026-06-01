from student_management.core.repository import BaseRepository
from student_management.models import Student


class StudentRepository(BaseRepository):
    model = Student
    select_related = ("course",)
