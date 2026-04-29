from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from student_management.custom.custom_api_exception import CustomException
from student_management.custom.custom_response import CustomResponse
from student_management.v1.serializers.auth_serializer import ChangePasswordSerializer


class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request):
        serializer = ChangePasswordSerializer(data=request.data, context={"request": request})

        if serializer.is_valid():
            serializer.save()
            return CustomResponse(
                message="Password changed successfully!",
                status=status.HTTP_200_OK,
            )

        raise CustomException(
            message="Fail to changed the password!", status_code=status.HTTP_400_BAD_REQUEST
        )
