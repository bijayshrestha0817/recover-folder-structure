from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated

from student_management.custom.custom_api_exception import CustomException
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


class PasswordResetRequestView(generics.CreateAPIView):
    def post(self, request, *args, **kwargs):
        email = request.data.get("email")
        user = get_object_or_404(User, email=email)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)

        reset_link = f"{settings.FRONTEND_URL}/auth/reset-password?uid={uid}&token={token}"

        send_mail(
            subject="Reset your password",
            message=f"Click the link to reset your password: {reset_link}",
            from_email="noreply@example.com",
            recipient_list=[email],
        )
        return CustomResponse(message="Reset link sent to you email!")


class PasswordResetConfirmView(generics.CreateAPIView):
    def post(self, request, *args, **kwargs):
        uid = force_str(urlsafe_base64_decode(request.data.get("uid")))
        token = request.data.get("token")
        new_password = request.data.get("new_password")

        user = get_object_or_404(User, pk=uid)

        if not default_token_generator.check_token(user, token):
            return CustomException(message="Invalid Token", status_code=status.HTTP_400_BAD_REQUEST)

        user.set_password(new_password)
        user.save()
        return CustomResponse(message="Password reset successfully!")
