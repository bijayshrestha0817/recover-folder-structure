import json

import pytest
from rest_framework import status

from student_management.models import Course

pytestmark = pytest.mark.django_db


# --- Create ---


def test_create_course(auth_client):
    response = auth_client.post(
        "/api/v1/courses/", json.dumps({"name": "Computer"}), content_type="application/json"
    )

    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["success"] is True
    assert Course.objects.filter(name="Computer").exists()


def test_create_course_duplicate_name_conflict(auth_client, course):
    response = auth_client.post(
        "/api/v1/courses/", json.dumps({"name": course.name}), content_type="application/json"
    )

    assert response.status_code == status.HTTP_409_CONFLICT
    assert response.json()["success"] is False


def test_create_course_validation_error(auth_client):
    response = auth_client.post("/api/v1/courses/", json.dumps({}), content_type="application/json")

    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_create_course_unauthenticated(client):
    response = client.post(
        "/api/v1/courses/", json.dumps({"name": "Computer"}), content_type="application/json"
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


# --- List ---


def test_list_course(auth_client, course):
    response = auth_client.get("/api/v1/courses/")

    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    assert body["success"] is True
    assert len(body["data"]["results"]) == 1


def test_list_course_empty_returns_404(auth_client):
    response = auth_client.get("/api/v1/courses/")

    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_course_dropdown_public(client, course):
    response = client.get("/api/v1/courses/all/")

    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()["data"]) == 1


# --- Detail ---


def test_course_detail(auth_client, course):
    response = auth_client.get(f"/api/v1/courses/{course.id}/")

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["data"]["id"] == course.id


def test_course_detail_not_found(auth_client, course):
    response = auth_client.get("/api/v1/courses/999999/")

    assert response.status_code == status.HTTP_404_NOT_FOUND


# --- Update ---


def test_course_update(auth_client, course):
    response = auth_client.put(
        f"/api/v1/courses/{course.id}/",
        json.dumps({"name": "updated course"}),
        content_type="application/json",
    )

    assert response.status_code == status.HTTP_200_OK
    course.refresh_from_db()
    assert course.name == "updated course"


def test_course_update_duplicate_name_conflict(auth_client, course):
    other = Course.objects.create(name="Physics")

    response = auth_client.put(
        f"/api/v1/courses/{other.id}/",
        json.dumps({"name": course.name}),
        content_type="application/json",
    )

    assert response.status_code == status.HTTP_409_CONFLICT


# --- Delete ---


def test_delete_course(auth_client, course):
    response = auth_client.delete(f"/api/v1/courses/{course.id}/")

    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert not Course.objects.filter(id=course.id).exists()


# --- Filtering / search / ordering ---


def test_list_course_search(auth_client):
    Course.objects.create(name="Maths")
    Course.objects.create(name="Physics")

    response = auth_client.get("/api/v1/courses/?search=phys")

    assert response.status_code == status.HTTP_200_OK
    results = response.json()["data"]["results"]
    assert len(results) == 1
    assert results[0]["name"] == "Physics"


def test_list_course_ordering(auth_client):
    Course.objects.create(name="Biology")
    Course.objects.create(name="Algebra")

    response = auth_client.get("/api/v1/courses/?ordering=name")

    assert response.status_code == status.HTTP_200_OK
    names = [r["name"] for r in response.json()["data"]["results"]]
    assert names == sorted(names)
