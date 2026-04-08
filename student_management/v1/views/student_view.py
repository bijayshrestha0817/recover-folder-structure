from rest_framework import generics

from student_management.v1.serializers.student_serializer import StudentSerializer
from student_management.v1.services.student_service import StudentService


class StudentView(generics.ListCreateAPIView):
    serializer_class = StudentSerializer

    def get_queryset(self):
        service = StudentService()
        return service.list_students()

    def perform_create(self, serializer):
        service = StudentService()
        service.create_student(serializer.validated_data)


class StudentDetails(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = StudentSerializer

    def get_queryset(self):
        service = StudentService()
        return service.list_students()

    def perform_create(self, serializer):
        service = StudentService()
        service.create_student(serializer.validated_data)
