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

    # --- query builder (read) ---

    def get_queryset(self) -> QuerySet:
        """Base queryset with the configured relations pre-joined."""
        queryset = self.model._default_manager.all()
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
        return self.model._default_manager.filter(**kwargs).exists()

    # --- mutations (write) ---

    def create(self, data: dict):
        return self.model._default_manager.create(**data)

    def update(self, instance, data: dict):
        for field, value in data.items():
            setattr(instance, field, value)
        instance.save()
        return instance

    def delete(self, instance) -> None:
        instance.delete()
