import json

import pytest
from rest_framework import status

from student_management.models import Student

pytestmake = pytest.mark.django_db


def test_create_student(auth_client, student_data):
    response = auth_client.post(
        "/api/v1/students/", data=json.dumps(student_data), content_type="application/json"
    )

    assert response.status_code == status.HTTP_201_CREATED


def test_list_student(auth_client, student_data, course):
    Student.objects.create(**{**student_data, "course": course})
    response = auth_client.get("/api/v1/students/")

    assert response.status_code == status.HTTP_200_OK

    data = json.loads(response.content)
    assert len(data["results"]) == 1


def test_student_details(auth_client, student_data, course):
    student = Student.objects.create(**{**student_data, "course": course})

    response = auth_client.get(f"/api/v1/students/{student.id}/")

    assert response.status_code == status.HTTP_200_OK


def test_update_student(auth_client, student_data, course):
    student = Student.objects.create(**{**student_data, "course": course})

    updated_data = {**student_data, "name": "updated name"}

    response = auth_client.put(
        f"/api/v1/students/{student.id}/",
        data=json.dumps(updated_data),
        content_type="application/json",
    )

    assert response.status_code == status.HTTP_200_OK


def test_delete_student(auth_client, student_data, course):
    student = Student.objects.create(**{**student_data, "course": course})

    response = auth_client.delete(f"/api/v1/students/{student.id}/")

    assert response.status_code == status.HTTP_204_NO_CONTENT
