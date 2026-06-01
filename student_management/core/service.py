from django.db import transaction
from rest_framework import status

from student_management.custom.custom_api_exception import CustomException


class BaseService:
    """Generic business-logic layer over a :class:`BaseRepository`.

    Subclass it and point at a repository::

        class CourseService(BaseService):
            repository_class = CourseRepository
            entity_name = "Course"
            unique_field = "name"   # optional: enforce uniqueness with a 409

    Provides ``list``/``get``/``create``/``update``/``delete`` with consistent
    ``CustomException`` errors (404 when empty/missing, 409 on duplicate).
    """

    repository_class: "type | None" = None
    entity_name: str = "Resource"
    unique_field: "str | None" = None

    def __init__(self) -> None:
        repository_class = self.repository_class
        if repository_class is None:
            raise NotImplementedError(f"{type(self).__name__} must define `repository_class`.")
        self.repo = repository_class()

    def get_all(self):
        """Full queryset (no emptiness check) — used by detail/get_object views."""
        return self.repo.all()

    def list(self):
        queryset = self.repo.all()
        if not queryset.exists():
            raise CustomException(
                message=f"No {self.entity_name} Found",
                status_code=status.HTTP_404_NOT_FOUND,
            )
        return queryset

    def get(self, pk):
        instance = self.repo.get_by_id(pk)
        if instance is None:
            raise CustomException(
                message=f"{self.entity_name} not found",
                status_code=status.HTTP_404_NOT_FOUND,
            )
        return instance

    @transaction.atomic
    def create(self, validated_data):
        self._ensure_unique(validated_data)
        return self.repo.create(validated_data)

    @transaction.atomic
    def update(self, instance, validated_data):
        self._ensure_unique(validated_data, exclude_pk=instance.pk)
        return self.repo.update(instance, validated_data)

    @transaction.atomic
    def delete(self, instance):
        return self.repo.delete(instance)

    def _ensure_unique(self, data, exclude_pk=None) -> None:
        if not self.unique_field or self.unique_field not in data:
            return
        queryset = self.repo.filter(**{self.unique_field: data[self.unique_field]})
        if exclude_pk is not None:
            queryset = queryset.exclude(pk=exclude_pk)
        if queryset.exists():
            raise CustomException(
                message=f"{self.entity_name} with this {self.unique_field} already exists",
                status_code=status.HTTP_409_CONFLICT,
            )
