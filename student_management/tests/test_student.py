import json

import pytest
from rest_framework import status

from student_management.models import Student

pytestmark = pytest.mark.django_db


# --- Create ---


def test_create_student(auth_client, student_data):
    response = auth_client.post(
        "/api/v1/students/", data=json.dumps(student_data), content_type="application/json"
    )

    assert response.status_code == status.HTTP_201_CREATED
    body = response.json()
    assert body["success"] is True
    assert body["data"]["email"] == student_data["email"]
    assert Student.objects.filter(email=student_data["email"]).exists()


def test_create_student_duplicate_email_rejected(auth_client, student_data, student):
    # Student.email is unique=True, so DRF's UniqueValidator rejects at 400 (serializer)
    # before the service-level 409 check is reached.
    response = auth_client.post(
        "/api/v1/students/", data=json.dumps(student_data), content_type="application/json"
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["success"] is False


def test_create_student_validation_error(auth_client, course):
    invalid = {"name": "No Age", "email": "noage@example.com", "course": course.id}

    response = auth_client.post(
        "/api/v1/students/", data=json.dumps(invalid), content_type="application/json"
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["success"] is False


def test_create_student_unauthenticated(client, student_data):
    response = client.post(
        "/api/v1/students/", data=json.dumps(student_data), content_type="application/json"
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


# --- List ---


def test_list_student(auth_client, student):
    response = auth_client.get("/api/v1/students/")

    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    assert body["success"] is True
    assert len(body["data"]["results"]) == 1


def test_list_student_empty_returns_404(auth_client):
    response = auth_client.get("/api/v1/students/")

    assert response.status_code == status.HTTP_404_NOT_FOUND


# --- Detail ---


def test_student_details(auth_client, student):
    response = auth_client.get(f"/api/v1/students/{student.id}/")

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["data"]["id"] == student.id


def test_student_details_not_found(auth_client, student):
    response = auth_client.get("/api/v1/students/999999/")

    assert response.status_code == status.HTTP_404_NOT_FOUND


# --- Update ---


def test_update_student(auth_client, student, student_data):
    updated_data = {**student_data, "name": "updated name"}

    response = auth_client.put(
        f"/api/v1/students/{student.id}/",
        data=json.dumps(updated_data),
        content_type="application/json",
    )

    assert response.status_code == status.HTTP_200_OK
    student.refresh_from_db()
    assert student.name == "updated name"


def test_update_student_duplicate_email_rejected(auth_client, course, student):
    other = Student.objects.create(name="Other", age=22, email="other@example.com", course=course)
    payload = {"name": other.name, "age": other.age, "email": student.email, "course": course.id}

    # Same as create: the unique email constraint is enforced by the serializer at 400.
    response = auth_client.put(
        f"/api/v1/students/{other.id}/",
        data=json.dumps(payload),
        content_type="application/json",
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST


# --- Delete ---


def test_delete_student(auth_client, student):
    response = auth_client.delete(f"/api/v1/students/{student.id}/")

    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert not Student.objects.filter(id=student.id).exists()
