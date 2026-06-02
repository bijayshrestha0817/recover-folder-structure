import json

import pytest
from rest_framework import status

from student_management.models import Student

pytestmark = pytest.mark.django_db


# --- Audit fields (created_by / updated_by) ---


def test_create_stamps_created_by(auth_client, user, student_data):
    response = auth_client.post(
        "/api/v1/students/", data=json.dumps(student_data), content_type="application/json"
    )

    assert response.status_code == status.HTTP_201_CREATED
    created = Student.objects.get(email=student_data["email"])
    assert created.created_by_id == user.id
    assert created.updated_by_id == user.id


def test_update_stamps_updated_by_only(auth_client, user, student):
    # A pre-existing row created outside the request has no created_by.
    assert student.created_by_id is None

    response = auth_client.patch(
        f"/api/v1/students/{student.id}/",
        data=json.dumps({"name": "Renamed"}),
        content_type="application/json",
    )

    assert response.status_code == status.HTTP_200_OK
    student.refresh_from_db()
    assert student.updated_by_id == user.id
    assert student.created_by_id is None  # untouched on update


# --- Soft delete ---


def test_delete_is_soft(auth_client, student):
    response = auth_client.delete(f"/api/v1/students/{student.id}/")

    assert response.status_code == status.HTTP_204_NO_CONTENT
    student.refresh_from_db()
    assert student.is_deleted is True
    assert student.deleted_at is not None


def test_soft_deleted_hidden_from_list_and_detail(auth_client, student):
    auth_client.delete(f"/api/v1/students/{student.id}/")

    detail = auth_client.get(f"/api/v1/students/{student.id}/")
    assert detail.status_code == status.HTTP_404_NOT_FOUND

    listing = auth_client.get("/api/v1/students/")
    # No live students remain -> service raises the empty-list 404.
    assert listing.status_code == status.HTTP_404_NOT_FOUND


def test_soft_deleted_row_still_in_database(auth_client, student):
    auth_client.delete(f"/api/v1/students/{student.id}/")

    # The default manager has no soft-delete filter, so the row is still present.
    assert Student.objects.filter(id=student.id, is_deleted=True).exists()


def test_restore_brings_row_back(auth_client, student):
    auth_client.delete(f"/api/v1/students/{student.id}/")
    student.refresh_from_db()

    student.restore()

    assert student.is_deleted is False
    assert student.deleted_at is None
    assert auth_client.get(f"/api/v1/students/{student.id}/").status_code == status.HTTP_200_OK
