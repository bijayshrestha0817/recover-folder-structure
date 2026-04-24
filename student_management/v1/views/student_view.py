from drf_spectacular.utils import extend_schema
from rest_framework import generics, status

from student_management.custom.custom_response import CustomResponse
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
    service = StudentService()

    def get_queryset(self):
        return self.service.list_students()

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return CustomResponse(
                data=self.get_paginated_response(serializer.data).data,
                message="Student fetched successfully",
                status=status.HTTP_200_OK,
            )
        serializer = self.get_serializer(queryset, many=True)
        return CustomResponse(
            data={"count": queryset.count, "results": serializer.data},
            message="Student fetched successfully",
            status=status.HTTP_200_OK,
        )

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        student = self.service.create_student(serializer.validated_data)
        return CustomResponse(
            data=StudentSerializer(student).data,
            message="Student created successfully",
            status=status.HTTP_201_CREATED,
        )


@extend_schema(tags=["Student"])
class StudentDetails(generics.RetrieveUpdateDestroyAPIView):
    # permission_classes = [IsAuthenticated]
    serializer_class = StudentSerializer
    service = StudentService()

    def get_queryset(self):
        return self.service.list_students()

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return CustomResponse(
            data=serializer.data,
            message="Student details fetched successfully",
            status=status.HTTP_200_OK,
        )

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        student = self.service.update_student(instance, serializer.validated_data)
        return CustomResponse(
            data=StudentSerializer(student).data,
            message="Student updated successfully",
            status=status.HTTP_200_OK,
        )

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.service.delete_student(instance)
        return CustomResponse(
            message="Student deleted successfully", status=status.HTTP_204_NO_CONTENT
        )
