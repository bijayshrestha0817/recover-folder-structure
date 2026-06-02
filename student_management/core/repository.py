from django.db.models import Model, QuerySet


class BaseRepository:
    """Generic data-access layer with query-builder helpers and CRUD.

    Subclass it and set ``model`` (required) plus optional relation hints so the
    base queryset is always optimized (no N+1) for the module's serializer::

        class StudentRepository(BaseRepository):
            model = Student
            select_related = ("course",)

    The read helpers (``all``, ``filter``, ``exclude``) return a ``QuerySet``, so
    they stay chainable just like the ORM::

        repo.filter(age__gte=18).exclude(course__isnull=True).order_by("-id")
    """

    model: "type[Model] | None" = None
    select_related: tuple[str, ...] = ()
    prefetch_related: tuple[str, ...] = ()

    def __init__(self) -> None:
        if self.model is None:
            raise NotImplementedError(f"{type(self).__name__} must define `model`.")

    # --- soft-delete / audit awareness ---

    def _has_field(self, name: str) -> bool:
        return any(field.name == name for field in self.model._meta.fields)

    @property
    def _soft_delete(self) -> bool:
        return self._has_field("is_deleted")

    @property
    def _audited(self) -> bool:
        return self._has_field("created_by")

    # --- query builder (read) ---

    def get_queryset(self) -> QuerySet:
        """Base queryset with the configured relations pre-joined.

        Soft-deleted rows are hidden here (query-shaping stays in this layer), so
        every read helper, list, and detail lookup only ever sees live records.
        """
        queryset = self.model._default_manager.all()
        if self._soft_delete:
            queryset = queryset.filter(is_deleted=False)
        if self.select_related:
            queryset = queryset.select_related(*self.select_related)
        if self.prefetch_related:
            queryset = queryset.prefetch_related(*self.prefetch_related)
        return queryset

    def all(self) -> QuerySet:
        return self.get_queryset()

    def filter(self, **kwargs) -> QuerySet:
        return self.get_queryset().filter(**kwargs)

    def exclude(self, **kwargs) -> QuerySet:
        return self.get_queryset().exclude(**kwargs)

    def get_by_id(self, pk):
        """Return the instance with ``pk`` or ``None`` (no exception)."""
        return self.get_queryset().filter(pk=pk).first()

    def exists(self, **kwargs) -> bool:
        queryset = self.model._default_manager.filter(**kwargs)
        if self._soft_delete:
            queryset = queryset.filter(is_deleted=False)
        return queryset.exists()

    # --- mutations (write) ---

    def create(self, data: dict, user=None):
        if self._audited and user is not None:
            data = {**data, "created_by": user, "updated_by": user}
        return self.model._default_manager.create(**data)

    def update(self, instance, data: dict, user=None):
        for field, value in data.items():
            setattr(instance, field, value)
        if self._audited and user is not None:
            instance.updated_by = user
        instance.save()
        return instance

    def delete(self, instance, user=None) -> None:
        """Soft-delete when the model supports it, otherwise remove the row."""
        if hasattr(instance, "soft_delete"):
            instance.soft_delete(user=user)
        else:
            instance.delete()
