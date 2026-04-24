from drf_spectacular.utils import extend_schema
from rest_framework import generics, pagination, status

from student_management.custom.custom_response import CustomResponse
from student_management.v1.serializers.course_serializer import CourseSerializer
from student_management.v1.services.course_service import CourseService


class CoursePagination(pagination.PageNumberPagination):
    page_size = 10


@extend_schema(tags=["Course"])
class CourseView(generics.ListCreateAPIView):
    serializer_class = CourseSerializer
    pagination_class = CoursePagination
    service = CourseService()

    def get_queryset(self):
        return self.service.list_course()

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()

        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = self.get_serializer(page, many=True)

            return CustomResponse(
                data=self.get_paginated_response(serializer.data).data,
                message="Course fetched successfully",
                status=status.HTTP_200_OK,
            )

        serializer = self.get_serializer(queryset, many=True)
        return CustomResponse(
            data={"count": queryset.count, "results": serializer.data},
            message="Course fetched successfully",
            status=status.HTTP_200_OK,
        )

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        course = self.service.create_course(serializer.validated_data)
        return CustomResponse(
            data=CourseSerializer(course).data,
            message="Course created successfully",
            status=status.HTTP_201_CREATED,
        )


@extend_schema(tags=["Course"])
class CourseDropdownAPIView(generics.ListAPIView):
    serializer_class = CourseSerializer
    pagination_class = None
    service = CourseService()

    def get_queryset(self):
        return self.service.list_course()

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)

        return CustomResponse(
            data=serializer.data,
            message="Dropdown data fetched",
        )


@extend_schema(tags=["Course"])
class CourseDetails(generics.RetrieveUpdateDestroyAPIView):
    # permission_classes = [IsAuthenticated]
    serializer_class = CourseSerializer
    service = CourseService()

    def get_queryset(self):
        return self.service.list_course()

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return CustomResponse(
            data=serializer.data,
            message="Course details fetched successfully",
            status=status.HTTP_200_OK,
        )

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        course = self.service.update_course(instance, serializer.validated_data)
        return CustomResponse(
            data=CourseSerializer(course).data,
            message="Course updated successfully",
            status=status.HTTP_200_OK,
        )

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.service.delete_course(instance)
        return CustomResponse(
            message="Course deleted successfully", status=status.HTTP_204_NO_CONTENT
        )
