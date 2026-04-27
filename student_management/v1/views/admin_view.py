from django.contrib.auth.models import User
from drf_spectacular.utils import extend_schema
from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from student_management.v1.serializers.admin_serializer import AdminSerializer
from student_management.v1.serializers.auth_serializer import RegisterSerializer
from student_management.v1.services.admin_service import AdminService


@extend_schema(tags=["Admin"])
class AdminViewList(generics.ListAPIView):
    serializer_class = AdminSerializer

    def get_queryset(self):
        service = AdminService()
        return service.list_admin()


@extend_schema(tags=["Admin"])
class AdminView(generics.CreateAPIView):
    serializer_class = AdminSerializer

    def get_queryset(self):
        service = AdminService()
        return service.list_admin()

    def perform_create(self, serializer):
        service = AdminService()
        service.create_admin(serializer.validated_data)


@extend_schema(tags=["Admin"])
class AdminDetails(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = AdminSerializer

    def get_queryset(self):
        service = AdminService()
        return service.list_admin()

    def perform_create(self, serializer):
        service = AdminService()
        service.create_admin(serializer.validated_data)


@extend_schema(tags=["Admin"])
class AdminLogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        service = AdminService()
        result = service.logout_admin(request)
        return Response(result, status=status.HTTP_200_OK)


@extend_schema(tags=["Admin"])
class AdminMeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = AdminSerializer(request.user)
        return Response(serializer.data)


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]
