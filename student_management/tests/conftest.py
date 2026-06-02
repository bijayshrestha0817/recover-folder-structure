import pytest
from django.contrib.auth.models import User
from django.core.cache import cache
from django.test import Client
from rest_framework_simplejwt.tokens import RefreshToken

from student_management.models import Course, Student


@pytest.fixture(autouse=True)
def _clear_throttle_cache():
    """Reset the rate-limit counters (kept in the cache) around every test so
    throttle state from one test never bleeds into the next."""
    cache.clear()
    yield
    cache.clear()


@pytest.fixture
def client():
    return Client()


@pytest.fixture
def user(db):
    return User.objects.create_user(username="testuser", password="testpassword")


@pytest.fixture
def auth_client(client, user):
    refresh_token = RefreshToken.for_user(user)
    access_token = str(refresh_token.access_token)

    client.defaults["HTTP_AUTHORIZATION"] = f"Bearer {access_token}"
    return client


@pytest.fixture
def admin_user(db):
    return User.objects.create_superuser(
        username="adminuser", email="admin@example.com", password="adminpassword123"
    )


@pytest.fixture
def admin_client(admin_user):
    client = Client()
    refresh_token = RefreshToken.for_user(admin_user)
    client.defaults["HTTP_AUTHORIZATION"] = f"Bearer {refresh_token.access_token}"
    return client


@pytest.fixture
def course(db):
    return Course.objects.create(name="Maths")


@pytest.fixture
def student_data(course):
    return {"name": "John Doe", "age": 20, "email": "john@gmail.com", "course": course.id}


@pytest.fixture
def student(course):
    return Student.objects.create(name="John Doe", age=20, email="john@gmail.com", course=course)
