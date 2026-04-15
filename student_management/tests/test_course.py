import json

import pytest
from rest_framework import status

pytestmark = pytest.mark.django_db


def test_create_course(auth_client):
    response = auth_client.post(
        "/api/v1/courses/", json.dumps({"name": "Computer"}), content_type="application/json"
    )
    assert response.status_code == status.HTTP_201_CREATED


def test_list_course(auth_client, course):
    response = auth_client.get("/api/v1/courses/")

    assert response.status_code == status.HTTP_200_OK

    data = json.loads(response.content)
    assert len(data["results"]) == 1


def test_course_detail(auth_client, course):
    response = auth_client.get(f"/api/v1/courses/{course.id}/")

    assert response.status_code == status.HTTP_200_OK


def test_course_update(auth_client, course):
    update_data = {"name": "updated course"}

    response = auth_client.put(
        f"/api/v1/courses/{course.id}/", json.dumps(update_data), content_type="application/json"
    )

    assert response.status_code == status.HTTP_200_OK


def test_delete_course(auth_client, course):
    response = auth_client.delete(f"/api/v1/courses/{course.id}/")

    assert response.status_code == status.HTTP_204_NO_CONTENT
