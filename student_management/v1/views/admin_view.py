from drf_spectacular.utils import extend_schema
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from student_management.v1.serializers.admin_serializer import AdminSerializer
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
        return Response(result, status=status.HTTP_200_OK)
        return Response(result, status=status.HTTP_200_OK)
