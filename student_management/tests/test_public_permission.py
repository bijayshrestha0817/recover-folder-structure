import pytest
from rest_framework import status

pytestmark = pytest.mark.django_db


def test_public_student_api(client):
    response = client.get("/api/v1/student-list/")

    assert response.status_code == status.HTTP_200_OK


def test_public_course_api(client):
    response = client.get("/api/v1/course-list/")

    assert response.status_code == status.HTTP_200_OK


def test_protected_student_api(client):
    response = client.get("/api/v1/students/")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
