from rest_framework import generics

from student_management.v1.serializers.course_serializer import CourseSerializer
from student_management.v1.services.course_service import CourseService
from student_management.v1.services.student_service import StudentService

class CourseView(generics.ListCreateAPIView):
    serializer_class = CourseSerializer

    def get_queryset(self):
        return CourseService.list_course()

    def perform_create(self, serializer):
        CourseService.create_course(serializer.validated_data)


class CourseDetails(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = CourseSerializer

    def get_queryset(self):
        return CourseService.list_course()
    
    def preform_create(self, serializer):
        CourseService.create_course(serializer.validated_data)