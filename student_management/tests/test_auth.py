import json

import pytest
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.core import mail
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from rest_framework import status

pytestmark = pytest.mark.django_db


# --- Token ---


def test_obtain_token(client):
    User.objects.create_user(username="testuser", password="testpassword")
    response = client.post(
        "/auth/token/",
        data={"username": "testuser", "password": "testpassword"},
        content_type="application/json",
    )

    assert response.status_code == status.HTTP_200_OK


# --- Change password (IsAuthenticated) ---


def test_change_password_success(auth_client, user):
    response = auth_client.put(
        "/auth/change-password/",
        data=json.dumps({"current_password": "testpassword", "new_password": "NewStrongPass123"}),
        content_type="application/json",
    )

    assert response.status_code == status.HTTP_200_OK
    user.refresh_from_db()
    assert user.check_password("NewStrongPass123")


def test_change_password_wrong_current(auth_client):
    response = auth_client.put(
        "/auth/change-password/",
        data=json.dumps({"current_password": "wrong", "new_password": "NewStrongPass123"}),
        content_type="application/json",
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["success"] is False


def test_change_password_reuse_old(auth_client):
    response = auth_client.put(
        "/auth/change-password/",
        data=json.dumps({"current_password": "testpassword", "new_password": "testpassword"}),
        content_type="application/json",
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_change_password_unauthenticated(client):
    response = client.put(
        "/auth/change-password/",
        data=json.dumps({"current_password": "x", "new_password": "y"}),
        content_type="application/json",
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


# --- Password reset request (public) ---


def test_reset_request_sends_email(client, settings):
    settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
    User.objects.create_user(username="u", email="u@example.com", password="testpassword")

    response = client.post(
        "/auth/reset-password/",
        data=json.dumps({"email": "u@example.com"}),
        content_type="application/json",
    )

    assert response.status_code == status.HTTP_200_OK
    assert len(mail.outbox) == 1


def test_reset_request_unknown_email(client):
    response = client.post(
        "/auth/reset-password/",
        data=json.dumps({"email": "missing@example.com"}),
        content_type="application/json",
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND


# --- Password reset confirm (public) ---


def test_reset_confirm_success(client):
    user = User.objects.create_user(username="u", email="u@example.com", password="testpassword")
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)

    response = client.post(
        "/auth/reset-password-confirm/",
        data=json.dumps({"uid": uid, "token": token, "new_password": "BrandNewPass123"}),
        content_type="application/json",
    )

    assert response.status_code == status.HTTP_200_OK
    user.refresh_from_db()
    assert user.check_password("BrandNewPass123")


def test_reset_confirm_invalid_uid(client):
    response = client.post(
        "/auth/reset-password-confirm/",
        data=json.dumps({"uid": "!!!bad!!!", "token": "x", "new_password": "BrandNewPass123"}),
        content_type="application/json",
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_reset_confirm_invalid_token(client):
    user = User.objects.create_user(username="u", email="u@example.com", password="testpassword")
    uid = urlsafe_base64_encode(force_bytes(user.pk))

    response = client.post(
        "/auth/reset-password-confirm/",
        data=json.dumps({"uid": uid, "token": "invalid-token", "new_password": "BrandNewPass123"}),
        content_type="application/json",
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
