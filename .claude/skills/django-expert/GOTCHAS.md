# Common Gotchas

## Table of Contents
- [Tenant Context in Celery Tasks](#1-tenant-context-in-celery-tasks)
- [QueryDict Multi-Value Params](#2-querydict-multi-value-params)
- [Bulk Operations Without History](#3-bulk-operations-without-history)
- [Missing Transaction on Multi-Step Mutations](#4-missing-transaction-on-multi-step-mutations)
- [Queries in Serializers](#5-queries-in-serializers)
- [Cross-Tenant Operations](#6-cross-tenant-operations)

---

## 1. Tenant Context in Celery Tasks

**Wrong:**
```python
@shared_task
def process_claims(project_id):
    claims = ClaimRecord.objects.all()  # Queries PUBLIC schema — empty or wrong data
```

**Right:**
```python
@shared_task
def process_claims(project_id, client_id):
    tenant = TenantRepository.get_tenant_object(project_id=project_id, client_id=client_id)
    with tenant_context(tenant):
        claims = ClaimRecord.objects.all()  # Queries tenant schema
```

## 2. QueryDict Multi-Value Params

**Wrong:**
```python
statuses = request.query_params.dict().get("status")  # Only gets LAST value
```

**Right:**
```python
statuses = request.query_params.getlist("status")  # Gets ALL values
```

## 3. Bulk Operations Without History

**Wrong:**
```python
ClaimRecord.objects.filter(id__in=ids).update(state_id=new_state)  # No audit trail
```

**Right:**
```python
from simple_history.utils import bulk_update_with_history
records = list(ClaimRecord.objects.filter(id__in=ids))
for r in records:
    r.state_id = new_state
bulk_update_with_history(records, ClaimRecord, ["state_id"], default_change_reason="State transition")
```

## 4. Missing Transaction on Multi-Step Mutations

**Wrong:**
```python
def update(entity, data):
    repo.update_entity(entity, data)         # Succeeds
    repo.create_audit_log(entity)            # Fails — entity is updated but no audit log
```

**Right:**
```python
@transaction.atomic
def update(entity, data):
    repo.update_entity(entity, data)
    repo.create_audit_log(entity)            # Both succeed or both roll back
```

## 5. Queries in Serializers

**Wrong:**
```python
class MySerializer(serializers.ModelSerializer):
    extra_data = serializers.SerializerMethodField()

    def get_extra_data(self, obj):
        return RelatedModel.objects.filter(parent=obj).first()  # N+1 on list endpoints
```

**Right (Prefetch with to_attr):**
```python
# Repository
queryset.prefetch_related(
    Prefetch(
        "related_set",
        queryset=RelatedModel.objects.order_by("-created_at"),
        to_attr="prefetched_related",
    )
)

# Serializer
def get_extra_data(self, obj):
    items = getattr(obj, "prefetched_related", [])
    return items[0] if items else None
```

**Right (Annotation):**
```python
# Repository — single value from related table
queryset.annotate(
    extra_data=Subquery(
        RelatedModel.objects.filter(parent=OuterRef("pk")).order_by("-created_at").values("value")[:1]
    )
)
```

## 6. Cross-Tenant Operations

When iterating across all tenants (e.g., scheduled cleanup tasks):

```python
tenants = TenantRepository.get_active_tenants()
for tenant in tenants:
    with tenant_context(tenant):
        # Operations scoped to this tenant's schema
        stale_sessions = AgentSession.objects.filter(end_time__isnull=True, ...)
```
