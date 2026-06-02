from django.conf import settings
from django.db import models
from django.utils import timezone


class AuditModel(models.Model):
    """Abstract base adding audit trail, timestamps, and soft delete.

    Subclass it instead of ``models.Model`` to get, for free::

        class Teacher(AuditModel):
            name = models.CharField(max_length=50)

    Fields:
      - ``created_at`` / ``updated_at`` — managed timestamps.
      - ``created_by`` / ``updated_by`` — the acting user (set by the repository
        from ``request.user``; ``editable=False`` so it never comes from input).
      - ``is_deleted`` / ``deleted_at`` — soft-delete marker.

    Query-shaping (hiding soft-deleted rows) lives in ``BaseRepository``, per the
    project's layering — this model only stores the fields and the
    ``soft_delete``/``restore`` behaviour. The default manager is left untouched
    on purpose so reverse relations and cascades keep seeing every row.
    """

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        editable=False,
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        editable=False,
    )
    is_deleted = models.BooleanField(default=False, db_index=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        abstract = True

    def soft_delete(self, user=None) -> None:
        """Mark the row deleted without removing it from the database."""
        self.is_deleted = True
        self.deleted_at = timezone.now()
        update_fields = ["is_deleted", "deleted_at", "updated_at"]
        if user is not None:
            self.updated_by = user
            update_fields.append("updated_by")
        self.save(update_fields=update_fields)

    def restore(self) -> None:
        """Reverse a soft delete."""
        self.is_deleted = False
        self.deleted_at = None
        self.save(update_fields=["is_deleted", "deleted_at", "updated_at"])
