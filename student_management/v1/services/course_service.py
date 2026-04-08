from student_management.repository.course_repository import CourseRepository


class CourseService:
    def list_course():
        return CourseRepository.get_all_courses()
    
    def create_course(validated_data):
        return CourseRepository.create_course(validated_data)