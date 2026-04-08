from rest_framework import generics

from student_management.v1.serializers.course_serializer import CourseSerializer
from student_management.v1.services.course_service import CourseService


class CourseView(generics.ListCreateAPIView):
    serializer_class = CourseSerializer

    def get_queryset(self):
        service = CourseService()
        return service.list_course()

    def perform_create(self, serializer):
        service = CourseService()
        service.create_course(serializer.validated_data)


class CourseDetails(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = CourseSerializer

    def get_queryset(self):
        service = CourseService()
        return service.list_course()

    def preform_create(self, serializer):
        service = CourseService()
        service.create_course(serializer.validated_data)
