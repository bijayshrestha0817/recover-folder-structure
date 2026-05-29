from django.contrib.auth.models import User
from drf_spectacular.utils import extend_schema
from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated
from rest_framework.views import APIView

from student_management.custom.custom_response import CustomResponse
from student_management.v1.serializers.admin_serializer import AdminSerializer
from student_management.v1.serializers.auth_serializer import RegisterSerializer
from student_management.v1.services.admin_service import AdminService


@extend_schema(tags=["Admin"])
class AdminViewList(generics.ListAPIView):
    permission_classes = [IsAdminUser]
    serializer_class = AdminSerializer

    def get_queryset(self):
        return AdminService().list_admin()


@extend_schema(tags=["Admin"])
class AdminView(generics.CreateAPIView):
    permission_classes = [IsAdminUser]
    serializer_class = AdminSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        admin = AdminService().create_admin(serializer.validated_data)
        return CustomResponse(
            data=AdminSerializer(admin).data,
            message="Admin created successfully",
            status=status.HTTP_201_CREATED,
        )


@extend_schema(tags=["Admin"])
class AdminDetails(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAdminUser]
    serializer_class = AdminSerializer

    def get_queryset(self):
        return AdminService().list_admin()


@extend_schema(tags=["Admin"])
class AdminLogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        result = AdminService().logout_admin(request)
        return CustomResponse(message=result["detail"], status=status.HTTP_200_OK)


@extend_schema(tags=["Admin"])
class AdminMeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = AdminSerializer(request.user)
        return CustomResponse(data=serializer.data, status=status.HTTP_200_OK)


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return CustomResponse(
            data=serializer.data,
            message="User registered successfully",
            status=status.HTTP_201_CREATED,
        )
