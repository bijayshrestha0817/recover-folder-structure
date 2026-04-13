from student_management.repository.admin_repository import AdminRepository


class AdminService:
    def list_admin(self):
        repo = AdminRepository()
        return repo.get_all_admins()

    def create_admin(self, validated_data):
        repo = AdminRepository()
        return repo.create_admin(validated_data)

    def logout_admin(self, request):
        repo = AdminRepository()
        return repo.logout_admin(request)
