import pytest
from django.contrib.auth.models import User
from django.test import Client
from rest_framework_simplejwt.tokens import RefreshToken

from student_management.models import Course


@pytest.fixture
def client():
    return Client()


@pytest.fixture
def user(db):
    return User.objects.create_user(username="testuser", password="testpassword")


@pytest.fixture
def auth_client():
    refresh_token = RefreshToken.for_user(user=user)
    access_token = str(refresh_token.access_token)

    client.defaults["HTTP_AUTHORIZATION"] = f"Bearer {access_token}"
    return client


@pytest.fixture
def course(db):
    return Course.objects.create(name="Maths")


@pytest.fixture
def student_data(course):
    return {"name": "John Doe", "age": 20, "email": "john@gmail.com", "course": course.id}
