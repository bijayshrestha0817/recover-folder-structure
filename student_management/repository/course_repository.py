from student_management.core.repository import BaseRepository
from student_management.models import Course


class CourseRepository(BaseRepository):
    model = Course
