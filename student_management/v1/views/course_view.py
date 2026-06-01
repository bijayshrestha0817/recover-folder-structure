from drf_spectacular.utils import extend_schema
from rest_framework import generics, pagination
from rest_framework.permissions import AllowAny, IsAuthenticated

from student_management.core.views import BaseListCreateView, BaseRetrieveUpdateDestroyView
from student_management.custom.custom_response import CustomResponse
from student_management.v1.serializers.course_serializer import CourseSerializer
from student_management.v1.services.course_service import CourseService


class CoursePagination(pagination.PageNumberPagination):
    page_size = 10


@extend_schema(tags=["Course"])
class CourseView(BaseListCreateView):
    permission_classes = [IsAuthenticated]
    serializer_class = CourseSerializer
    service_class = CourseService
    entity_name = "Course"
    pagination_class = CoursePagination
    search_fields = ["name"]
    ordering_fields = ["name", "id"]


@extend_schema(tags=["Course"])
class CourseDropdownAPIView(generics.ListAPIView):
    """Public, unpaginated list for dropdowns."""

    permission_classes = [AllowAny]
    serializer_class = CourseSerializer
    pagination_class = None

    def get_queryset(self):
        return CourseService().list()

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)

        return CustomResponse(
            data=serializer.data,
            message="Dropdown data fetched",
        )


@extend_schema(tags=["Course"])
class CourseDetails(BaseRetrieveUpdateDestroyView):
    permission_classes = [IsAuthenticated]
    serializer_class = CourseSerializer
    service_class = CourseService
    entity_name = "Course"
