import pytest
from rest_framework import status

pytestmark = pytest.mark.django_db


def test_public_student_api(client, student):
    """student-list/ is public (AllowAny)."""
    response = client.get("/api/v1/student-list/")

    assert response.status_code == status.HTTP_200_OK


def test_public_course_api(client, course):
    """courses/all/ (dropdown) is public (AllowAny)."""
    response = client.get("/api/v1/courses/all/")

    assert response.status_code == status.HTTP_200_OK


def test_protected_student_api(client):
    """students/ requires authentication."""
    response = client.get("/api/v1/students/")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_protected_course_api(client):
    """courses/ requires authentication."""
    response = client.get("/api/v1/courses/")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
