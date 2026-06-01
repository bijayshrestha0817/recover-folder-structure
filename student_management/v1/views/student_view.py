from drf_spectacular.utils import extend_schema
from rest_framework import generics
from rest_framework.permissions import AllowAny, IsAuthenticated

from student_management.core.views import BaseListCreateView, BaseRetrieveUpdateDestroyView
from student_management.v1.serializers.student_serializer import StudentSerializer
from student_management.v1.services.student_service import StudentService


@extend_schema(tags=["Student"])
class StudentViewList(generics.ListAPIView):
    """Public read-only list of students."""

    permission_classes = [AllowAny]
    serializer_class = StudentSerializer

    def get_queryset(self):
        return StudentService().list()


@extend_schema(tags=["Student"])
class StudentView(BaseListCreateView):
    permission_classes = [IsAuthenticated]
    serializer_class = StudentSerializer
    service_class = StudentService
    entity_name = "Student"
    filterset_fields = ["course"]
    search_fields = ["name", "email"]
    ordering_fields = ["name", "age", "id"]


@extend_schema(tags=["Student"])
class StudentDetails(BaseRetrieveUpdateDestroyView):
    permission_classes = [IsAuthenticated]
    serializer_class = StudentSerializer
    service_class = StudentService
    entity_name = "Student"
