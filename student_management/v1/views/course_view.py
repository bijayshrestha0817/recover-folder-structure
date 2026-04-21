from rest_framework import generics, pagination

from student_management.v1.serializers.course_serializer import CourseSerializer
from student_management.v1.services.course_service import CourseService


class CoursePagination(pagination.PageNumberPagination):
    page_size = 10


class CourseViewList(generics.ListAPIView):
    serializer_class = CourseSerializer
    pagination_class = CoursePagination

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


class CourseDropdownAPIView(generics.ListAPIView):
    serializer_class = CourseSerializer
    pagination_class = None

    def get_queryset(self):
        return CourseService().list_course()


class CourseDetails(generics.RetrieveUpdateDestroyAPIView):
    # permission_classes = [IsAuthenticated]
    serializer_class = CourseSerializer

    def get_queryset(self):
        service = CourseService()
        return service.list_course()

    def perform_create(self, serializer):
        service = CourseService()
        service.create_course(serializer.validated_data)
        service.create_course(serializer.validated_data)
