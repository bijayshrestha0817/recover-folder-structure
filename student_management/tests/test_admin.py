import json

import pytest
from django.contrib.auth.models import User
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

pytestmark = pytest.mark.django_db


# --- Admin list (IsAdminUser) ---


def test_admin_list_as_admin(admin_client, admin_user):
    response = admin_client.get("/api/v1/admin-list/")

    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()["results"]) == 1


def test_admin_list_forbidden_for_regular_user(auth_client):
    response = auth_client.get("/api/v1/admin-list/")

    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_admin_list_unauthenticated(client):
    response = client.get("/api/v1/admin-list/")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


# --- Create admin (IsAdminUser) ---


def test_create_admin_as_admin(admin_client):
    payload = {"username": "newadmin", "email": "newadmin@example.com", "password": "strongpass123"}

    response = admin_client.post(
        "/api/v1/auth/users/", data=json.dumps(payload), content_type="application/json"
    )

    assert response.status_code == status.HTTP_201_CREATED
    created = User.objects.get(username="newadmin")
    assert created.is_superuser
    # Password must never be echoed back.
    assert "password" not in response.json()["data"]


def test_create_admin_forbidden_for_regular_user(auth_client):
    payload = {"username": "hacker", "email": "hacker@example.com", "password": "strongpass123"}

    response = auth_client.post(
        "/api/v1/auth/users/", data=json.dumps(payload), content_type="application/json"
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert not User.objects.filter(username="hacker").exists()


# --- Me (IsAuthenticated) ---


def test_me_returns_current_user_without_password(auth_client, user):
    response = auth_client.get("/auth/me/")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()["data"]
    assert data["username"] == user.username
    assert "password" not in data


def test_me_unauthenticated(client):
    response = client.get("/auth/me/")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


# --- Register (public) ---


def test_register_public(client):
    payload = {"username": "registered", "email": "reg@example.com", "password": "strongpass123"}

    response = client.post("/register/", data=json.dumps(payload), content_type="application/json")

    assert response.status_code == status.HTTP_201_CREATED
    registered = User.objects.get(username="registered")
    assert not registered.is_superuser
    # create_user must hash the password (never store it in plaintext).
    assert registered.check_password("strongpass123")


def test_register_duplicate_email_rejected(client):
    # Email is the password-reset lookup key, so it must be unique (and
    # case-insensitively so) — otherwise a reset can target the wrong account.
    User.objects.create_user(username="first", email="dupe@example.com", password="strongpass123")
    payload = {"username": "second", "email": "DUPE@example.com", "password": "strongpass123"}

    response = client.post("/register/", data=json.dumps(payload), content_type="application/json")

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert not User.objects.filter(username="second").exists()


def test_register_blank_email_rejected(client):
    payload = {"username": "noemail", "email": "", "password": "strongpass123"}

    response = client.post("/register/", data=json.dumps(payload), content_type="application/json")

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert not User.objects.filter(username="noemail").exists()


# --- Logout (IsAuthenticated) ---


def test_logout_blacklists_refresh_token(admin_client, admin_user):
    refresh = RefreshToken.for_user(admin_user)

    response = admin_client.post(
        "/auth/logout/",
        data=json.dumps({"refresh": str(refresh)}),
        content_type="application/json",
    )

    assert response.status_code == status.HTTP_200_OK
