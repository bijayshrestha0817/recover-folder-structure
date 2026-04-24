from drf_spectacular.utils import extend_schema
from rest_framework import generics

from student_management.v1.serializers.student_serializer import StudentSerializer
from student_management.v1.services.student_service import StudentService


@extend_schema(tags=["Student"])
class StudentViewList(generics.ListAPIView):
    serializer_class = StudentSerializer

    def get_queryset(self):
        service = StudentService()
        return service.list_students()


@extend_schema(tags=["Student"])
class StudentView(generics.ListCreateAPIView):
    # permission_classes = [IsAuthenticated]
    serializer_class = StudentSerializer

    def get_queryset(self):
        service = StudentService()
        return service.list_students()

    def perform_create(self, serializer):
        service = StudentService()
        service.create_student(serializer.validated_data)


@extend_schema(tags=["Student"])
class StudentDetails(generics.RetrieveUpdateDestroyAPIView):
    # permission_classes = [IsAuthenticated]
    serializer_class = StudentSerializer

    def get_queryset(self):
        service = StudentService()
        return service.list_students()

    def perform_create(self, serializer):
        service = StudentService()
        service.create_student(serializer.validated_data)
