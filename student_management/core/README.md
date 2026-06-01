# Core CRUD Base

Reusable layered scaffolding so a new module gets full CRUD with almost no
boilerplate. Three base classes mirror the project's layers:

| Layer | Base class | File |
|-------|-----------|------|
| Repository (data access + query builder) | `BaseRepository` | `core/repository.py` |
| Service (business logic + errors) | `BaseService` | `core/service.py` |
| View (HTTP + `CustomResponse` envelope) | `BaseListCreateView`, `BaseRetrieveUpdateDestroyView` | `core/views.py` |

## Adding a new module (example: `Teacher`)

### 1. Model — `models.py`

```python
class Teacher(models.Model):
    name = models.CharField(max_length=50)
    email = models.EmailField(unique=True, db_index=True)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name="teachers")

    class Meta:
        ordering = ["-id"]

    def __str__(self):
        return self.name
```

### 2. Repository — `repository/teacher_repository.py`

```python
from student_management.core.repository import BaseRepository
from student_management.models import Teacher


class TeacherRepository(BaseRepository):
    model = Teacher
    select_related = ("department",)   # keeps list endpoints N+1-free
```

### 3. Service — `v1/services/teacher_service.py`

```python
from student_management.core.service import BaseService
from student_management.repository.teacher_repository import TeacherRepository


class TeacherService(BaseService):
    repository_class = TeacherRepository
    entity_name = "Teacher"
    unique_field = "email"   # optional: duplicate -> 409
```

### 4. Serializer — `v1/serializers/teacher_serializer.py`

```python
from rest_framework import serializers

from student_management.models import Teacher


class TeacherSerializer(serializers.ModelSerializer):
    department_name = serializers.CharField(source="department.name", read_only=True)

    class Meta:
        model = Teacher
        fields = ["id", "name", "email", "department", "department_name"]
```

### 5. Views — `v1/views/teacher_view.py`

```python
from drf_spectacular.utils import extend_schema
from rest_framework.permissions import IsAuthenticated

from student_management.core.views import BaseListCreateView, BaseRetrieveUpdateDestroyView
from student_management.v1.serializers.teacher_serializer import TeacherSerializer
from student_management.v1.services.teacher_service import TeacherService


@extend_schema(tags=["Teacher"])
class TeacherView(BaseListCreateView):
    permission_classes = [IsAuthenticated]
    serializer_class = TeacherSerializer
    service_class = TeacherService
    entity_name = "Teacher"


@extend_schema(tags=["Teacher"])
class TeacherDetails(BaseRetrieveUpdateDestroyView):
    permission_classes = [IsAuthenticated]
    serializer_class = TeacherSerializer
    service_class = TeacherService
    entity_name = "Teacher"
```

### 6. URLs — `v1/urls.py`

```python
path("teachers/", TeacherView.as_view()),
path("teachers/<int:pk>/", TeacherDetails.as_view()),
```

That's it — list (paginated), create, retrieve, update, and delete all work,
wrapped in the standard `CustomResponse` envelope with `404`/`409` handling.

## What you get for free

- **List** `GET` — paginated, `404 "No Teacher Found"` when empty.
- **Create** `POST` — `409` on duplicate `unique_field`, `201` on success.
- **Retrieve** `GET /<pk>/` — standard `404` for missing id.
- **Update** `PUT`/`PATCH` — duplicate check excludes the current row.
- **Delete** `DELETE /<pk>/` — `204`.

## Customizing

- **Override one method**: subclass a base view/service and override just the
  hook you need (e.g. a custom `create` for extra validation) — the rest stays.
- **Extra query logic**: add methods to the repository; `all()`, `filter()`,
  `exclude()` return chainable querysets:
  `repo.filter(active=True).order_by("-id")`.
- **Cross-field uniqueness / business rules**: override `BaseService._ensure_unique`
  or the relevant CRUD method.

## When NOT to use the base

Bespoke endpoints (auth, password reset, logout, anything that isn't plain
model CRUD) should stay hand-written — see the `admin`/`auth` modules. The base
is for the common "model in, model out" case, not a forced abstraction.
