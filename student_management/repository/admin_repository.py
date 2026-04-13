from django.contrib.auth.models import User
from rest_framework_simplejwt.tokens import RefreshToken


class AdminRepository:
    def get_all_admins(self):
        return User.objects.filter(is_superuser=True)

    def create_admin(self, data):
        return User.objects.create_superuser(**data)

    def logout_admin(self, request):
        """Logout the authenticated user."""
        refresh_token = request.data["refresh"]
        token = RefreshToken(refresh_token)
        token.blacklist()

        return {"detail": "Successfully logged out."}
