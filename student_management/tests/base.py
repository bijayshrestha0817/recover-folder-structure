from django.contrib.auth.models import User
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from student_management.models import Course


class BaseTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="test", password="test")

        self.course = Course.objects.create(name="Testing")

        refresh = RefreshToken.for_user(self.user)
        self.access_token = str(refresh.access_token)

        self.auth_header = {"HTTP_AUTHORIZATION": f"Bearer {self.access_token}"}
