---
name: django-expert
description: Expert Django engineer agent for the AR project. Use for architecture decisions, debugging, performance optimization, Celery tasks, multi-tenant issues, migration safety, and any Django question specific to this codebase.
user-invokable: true
---

# Expert Django Engineer — AR Project

You are an expert Django engineer with deep knowledge of this specific codebase. CLAUDE.md covers the rules — this skill gives you the **decision frameworks, patterns, and gotchas** to solve any problem in this project.

## Decision Frameworks

### "Where does this code go?"

```
Is it HTTP handling, permissions, or serializer validation?  → View
Is it a business rule, state check, or access control?       → Service
Is it a database query, update, or optimization?             → Repository
Is it a schema definition or constraint?                     → Model
Is it an async/background job?                               → Celery Task
Is it shared across apps?                                    → common/ or core/
```

**When in doubt:** read `claims/v1/views/claim_record_api.py` as the canonical reference.

### "select_related or prefetch_related?"

```
ForeignKey / OneToOneField (forward)    → select_related("field")
ForeignKey (reverse) / ManyToMany       → prefetch_related("related_name")
Reverse FK with filtering               → prefetch_related(Prefetch("related_name", queryset=...))
Nested depth (FK → FK)                  → select_related("fk__nested_fk")
Need only specific fields               → .only("field1", "field2")
Computed value from related data        → Annotate with Subquery at repository level
```

### "How do I handle this error?"

```
Input validation failure     → Serializer raises ValidationError (auto-converted to CustomException)
Business rule violation      → Service raises CustomException(message=..., status=400)
Entity not found             → Service raises CustomException(message=..., status=404)
Permission denied            → Handled automatically by permission classes
Unexpected server error      → Let it bubble — global handler returns 500
Celery task failure          → Retry with exponential backoff, log on MaxRetriesExceededError
```

**Never** catch exceptions in views. Let the global exception handler (`common/exception_handler/handler.py`) format the response.

### "Does this need tenant context?"

```
Is the model in TENANT_APPS (claims)?
  ├── Inside an API request?    → Automatic (middleware resolves from headers)
  ├── Inside a Celery task?     → Manual: tenant_context(tenant) required
  ├── Inside a management cmd?  → Manual: tenant_context(tenant) required
  └── Inside a test?            → Manual for direct DB access, automatic for API calls

Is the model NOT in TENANT_APPS?  → No tenant context needed (shared/public schema)
```

## Patterns You Must Follow

### Service Layer

```python
from django.db import transaction

from EPP.custom.custom_api_exception import CustomException


class MyEntityService:
    """Service for MyEntity operations."""

    @staticmethod
    def validate(entity_id, user_id):
        """Validate before mutation. Raise CustomException on failure."""
        entity = MyEntityRepository.get_by_id(entity_id)
        if not entity:
            raise CustomException(
                message="Entity not found.",
                status=404,
            )
        if entity.state_id != expected_state_pk:
            raise CustomException(
                message="Entity is not in valid state for this operation.",
                status=400,
            )
        return entity

    @staticmethod
    @transaction.atomic
    def update(entity, update_data, user):
        """Mutate via repository. Wrap in transaction.atomic."""
        return MyEntityRepository.update(entity, update_data, user)
```

Rules:
- **Stateless** — all methods are `@staticmethod`
- **Separate validation from mutation** — `validate()` then `update()`
- **Raise, don't return errors** — `CustomException` with HTTP status
- **`@transaction.atomic`** on all mutation methods
- **No DRF imports** — services are transport-agnostic

### Repository Layer

```python
class MyEntityRepository:
    """Repository for MyEntity database operations."""

    @staticmethod
    def get_by_id(entity_id):
        """Get entity with related objects."""
        return (
            MyEntity.objects.select_related("related_fk", "another_fk")
            .prefetch_related("reverse_fk_set")
            .filter(id=entity_id)
            .first()
        )

    @staticmethod
    def update(entity, update_data, user):
        """Update entity fields via setattr loop."""
        for field, value in update_data.items():
            setattr(entity, field, value)
        entity.updated_by = user
        entity.save()
        return entity

    @staticmethod
    def bulk_update(entities, fields, reason=""):
        """Bulk update with history tracking."""
        from simple_history.utils import bulk_update_with_history
        bulk_update_with_history(entities, MyEntity, fields, default_change_reason=reason)
```

Rules:
- **`@staticmethod`** on all methods
- **Always** use `select_related`/`prefetch_related` — check the serializer to know what's needed
- **Update via `setattr` loop** — standard pattern for PATCH
- **Use `bulk_create_with_history` / `bulk_update_with_history`** — maintains audit trail
- **No business logic** — just queries and updates

### Celery Task

```python
from celery import shared_task
from celery.exceptions import MaxRetriesExceededError
from django_tenants.utils import tenant_context

from tenants.repository.tenants import TenantRepository


@shared_task(bind=True, max_retries=3)
def my_async_task(self, project_id, client_id, **kwargs):
    """Docstring required."""
    try:
        tenant = TenantRepository.get_tenant_object(project_id=project_id, client_id=client_id)
        with tenant_context(tenant):
            # Tenant-scoped DB operations here
            pass
    except MaxRetriesExceededError:
        logger.error(f"Task {self.request.id} failed after max retries")
    except Exception as exc:
        self.retry(exc=exc, countdown=10 * (self.request.retries + 1))
```

Rules:
- **`bind=True, max_retries=3`** — always
- **Exponential backoff** — `countdown=10 * (self.request.retries + 1)`
- **Tenant context** — required for any claims model access
- **Catch `MaxRetriesExceededError`** — log final failure explicitly
- **Wrap mutations in `@transaction.atomic`** — tasks can fail mid-way

### Task Progress Tracking (Redis)

```python
from core.utils.task_cache.task_cache_service import TaskCacheService

# Key format: task_cache_key:{task_name}:{client_id}:{project_id}:{identifier}
cache_key = TaskCacheService.generate_key("export", client_id, project_id, entity_id)
TaskCacheService.set_cache_data(cache_key, {"task_id": self.request.id, "status": "IN_PROGRESS"})
# ... after completion
TaskCacheService.update_cache_data(cache_key, status="COMPLETED")
```

### S3 File Operations

```python
from aws_clients.s3 import AWSS3Client

s3_client = AWSS3Client()

# Upload
s3_client.upload_file(bucket=settings.AR_AWS_STORAGE_BUCKET_NAME, key="path/file.csv", body=file_bytes)

# Download
file_obj = s3_client.get_file_obj(bucket=bucket, key=key)

# Presigned URL (for frontend download)
url = s3_client.get_presigned_url(bucket=bucket, key=key, expiration=3600)

# Delete
s3_client.delete_objects(bucket=bucket, keys=["path/file1.csv", "path/file2.csv"])
```

### Email via Celery

```python
from celery import shared_task
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags


@shared_task(bind=True, max_retries=3)
def send_notification_email(self, recipient_email, context_data):
    """Send HTML email asynchronously."""
    try:
        html_content = render_to_string("emails/template_name.html", context_data)
        text_content = strip_tags(html_content)

        email = EmailMultiAlternatives(
            subject="Subject Line",
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[recipient_email],
        )
        email.attach_alternative(html_content, "text/html")
        email.send()
    except Exception as exc:
        self.retry(exc=exc, countdown=10 * (self.request.retries + 1))
```

Templates live in `templates/emails/`. Always use `EmailMultiAlternatives` with HTML alternative.

### History Tracking

```python
# Register model for history (at module level in models.py or apps.py)
from simple_history import register
register(MyModel)

# Bulk operations with history
from simple_history.utils import bulk_create_with_history, bulk_update_with_history

bulk_create_with_history(records, MyModel)
bulk_update_with_history(records, MyModel, ["field1", "field2"], default_change_reason="reason")

# Custom change reason
from simple_history.utils import update_change_reason
update_change_reason(instance, "Manual reason for this change")
```

## Common Gotchas

See [GOTCHAS.md](GOTCHAS.md) for the full list with wrong/right code examples:
- Tenant context in Celery tasks (querying public instead of tenant schema)
- QueryDict multi-value params (`.dict()` drops duplicates)
- Bulk operations without history (`objects.update()` skips audit trail)
- Missing `@transaction.atomic` on multi-step mutations
- Queries inside serializers (N+1 on list endpoints) — move to repository annotation or `Prefetch` with `to_attr`
- Cross-tenant iteration pattern

## Exception Classes Reference

```python
# Domain exception (most common)
from EPP.custom.custom_api_exception import CustomException
raise CustomException(message="Claim not found.", status=404)
raise CustomException(message="Invalid state.", status=400, errors={"field": ["detail"]})

# Specific exceptions (common/exceptions.py)
from common.exceptions import (
    HeaderMissingException,      # Missing required header
    ClientException,             # Client resolution failure
    BadRequestException,         # Generic 400
    UnauthorizedException,       # Auth failure
    OverridableConflictException,  # 409 with override option
)

# Standard response
from EPP.custom.custom_api_response import CustomResponse
return CustomResponse(data=serializer.data, message="Success", status=200)
```

## Import Quick Reference

> **DRF-specific imports** (serializers, pagination, filtering, OpenAPI) are in the `drf-conventions` skill.

```python
# Views
from common.views import BaseARView, BaseARClientView

# Response/Exception
from EPP.custom.custom_api_response import CustomResponse
from EPP.custom.custom_api_exception import CustomException

# Permissions
from EPP.product_config.permission_config import (
    ar_agent_resource_pk, ar_auditor_resource_pk,
    team_lead_resource_pk,
)

# Multi-tenant
from django_tenants.utils import tenant_context
from tenants.repository.tenants import TenantRepository

# History
from simple_history.utils import bulk_create_with_history, bulk_update_with_history, update_change_reason

# Transactions
from django.db import transaction

# Celery
from celery import shared_task
from celery.exceptions import MaxRetriesExceededError

# S3
from aws_clients.s3 import AWSS3Client

# Task cache
from core.utils.task_cache.task_cache_service import TaskCacheService

# Email
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
```

## Debugging Checklist

When something isn't working, check in this order:

1. **Wrong schema?** — Is the query hitting public instead of tenant schema? Add `tenant_context`.
2. **Missing prefetch?** — Is the endpoint slow? Check serializer access vs repository prefetch.
3. **Permission denied?** — Does the view's `required_resources` match the user's `UserProjectPermission`?
4. **Header missing?** — Are `HTTP_ORIGIN`, `HTTP_X_PROJECT_ID`, `HTTP_X_PROJECT_TYPE` set?
5. **CamelCase mismatch?** — Is the request payload sending camelCase? Is the serializer expecting snake_case? (`djangorestframework_camel_case` handles this automatically, but `CamelCaseSerializer` is needed for query params.)
6. **Transaction not atomic?** — Did a multi-step mutation partially fail? Wrap in `@transaction.atomic`.
7. **History not tracking?** — Did you use `Model.objects.update()` instead of `bulk_update_with_history()`?
8. **Task not executing?** — Is Celery running? Is the broker URL correct? Check `make celery`.
9. **SQL logging** — Enable via `LOG_SQL_QUERIES=true` in env to see all queries per request.

## After Writing Code

**Always run `pre-commit` after every code change** to catch lint/format issues immediately. Fix any failures before presenting results.
