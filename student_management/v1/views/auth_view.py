from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated

from student_management.custom.custom_response import CustomResponse
from student_management.v1.serializers.auth_serializer import ChangePasswordSerializer


class ChangePasswordView(generics.UpdateAPIView):
    permission_classes = [IsAuthenticated]

    def put(self, request):
        serializer = ChangePasswordSerializer(data=request.data, context={"request": request})

        serializer.is_valid(raise_exception=True)
        serializer.save()

        return CustomResponse(
            message="Password changed successfully!",
            status=status.HTTP_200_OK,
        )
