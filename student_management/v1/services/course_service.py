from student_management.core.service import BaseService
from student_management.repository.course_repository import CourseRepository


class CourseService(BaseService):
    repository_class = CourseRepository
    entity_name = "Course"
    unique_field = "name"
