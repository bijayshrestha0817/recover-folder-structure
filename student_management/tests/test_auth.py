import pytest
from django.contrib.auth.models import User
from rest_framework import status

pytestmark = pytest.mark.django_db


def test_obtain_token(client):
    User.objects.create_user(username="testuser", password="testpassword")
    response = client.post(
        "/auth/token/",
        data={"username": "testuser", "password": "testpassword"},
        content_type="application/json",
    )

    assert response.status_code == status.HTTP_200_OK
