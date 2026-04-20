from rest_framework import generics

from student_management.v1.serializers.course_serializer import CourseSerializer
from student_management.v1.services.course_service import CourseService


class CourseViewList(generics.ListAPIView):
    serializer_class = CourseSerializer

    def get_queryset(self):
        service = CourseService()
        return service.list_course()


class CourseView(generics.ListCreateAPIView):
    # permission_classes = [IsAuthenticated]

    serializer_class = CourseSerializer

    def get_queryset(self):
        service = CourseService()
        return service.list_course()

    def perform_create(self, serializer):
        service = CourseService()
        service.create_course(serializer.validated_data)


class CourseDetails(generics.RetrieveUpdateDestroyAPIView):
    # permission_classes = [IsAuthenticated]
    serializer_class = CourseSerializer

    def get_queryset(self):
        service = CourseService()
        return service.list_course()

    def perform_create(self, serializer):
        service = CourseService()
        service.create_course(serializer.validated_data)
