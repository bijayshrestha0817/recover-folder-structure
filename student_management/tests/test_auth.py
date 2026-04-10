from django.contrib.auth.models import User
from rest_framework.test import APITestCase


class AuthTest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="test")

    def test_obtain_token(self):
        response = self.client.post("/api/token/", {"username": "testuser", "password": "test"})

        self.assertEqual(response.status_code, 200)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)
