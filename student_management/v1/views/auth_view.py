from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated

from student_management.custom.custom_api_exception import CustomException
from student_management.custom.custom_response import CustomResponse
from student_management.tasks import send_password_reset_email
from student_management.v1.serializers.auth_serializer import (
    ChangePasswordSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
)


class ChangePasswordView(generics.UpdateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ChangePasswordSerializer

    def put(self, request, *args, **kwargs):
        serializer = self.get_serializer(
            data=request.data,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return CustomResponse(
            message="Password changed successfully.",
            status=status.HTTP_200_OK,
        )


class PasswordResetRequestView(generics.CreateAPIView):
    permission_classes = [AllowAny]
    serializer_class = PasswordResetRequestSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]
        user = User.objects.filter(email=email).first()

        if not user:
            raise CustomException(
                message="User does not exist", status_code=status.HTTP_404_NOT_FOUND
            )

        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        reset_link = f"{settings.FRONTEND_URL}/reset-password?uid={uid}&token={token}"

        # Send off the request thread — the API responds immediately and the
        # email delivery (with retries) happens in a Celery worker.
        send_password_reset_email.delay(email, reset_link)

        return CustomResponse(
            message="Reset link has been sent to your email.",
            status=status.HTTP_200_OK,
        )


class PasswordResetConfirmView(generics.CreateAPIView):
    permission_classes = [AllowAny]
    serializer_class = PasswordResetConfirmSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        uid = serializer.validated_data["uid"]
        token = serializer.validated_data["token"]
        new_password = serializer.validated_data["new_password"]

        try:
            user_id = force_str(urlsafe_base64_decode(uid))
            user = User.objects.get(pk=user_id)
        except (ValueError, TypeError, OverflowError, User.DoesNotExist):
            raise CustomException(  # noqa: B904
                message="Invalid UID.",
                status_code=400,
            )

        if not default_token_generator.check_token(user, token):
            raise CustomException(
                message="Invalid or expired token.",
                status_code=400,
            )

        user.set_password(new_password)
        user.save()

        return CustomResponse(
            message="Password reset successfully. Please login.",
            status=status.HTTP_200_OK,
        )
