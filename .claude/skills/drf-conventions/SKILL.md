---
name: drf-conventions
description: DRF API conventions for the AR project. Use when asked to create, modify, or review Django REST Framework APIs, serializers, views, or endpoints.
user-invokable: true
---

# DRF Conventions — AR Project

CLAUDE.md (always in context) covers architecture rules, strict boundaries, and code style. This skill provides the **actionable recipes and project-specific imports** needed when writing DRF code.

## Steps to Create a New Endpoint

1. **Repository** — `<app>/repository/<entity>_repository.py`
2. **Service** — `<app>/v1/service/<entity>_service.py`
3. **Serializers** — `<app>/v1/serializers/<entity>_serializer.py` (or `<entity>.py`)
4. **View** — `<app>/v1/views/<feature>_api.py`
5. **URL** — wire into `<app>/v1/urls.py`
6. **URL chain** — route via `core/v1/urls.py` (if app is tenant-scoped) or `EPP/v1/urls.py` (if app is shared). *Check `TENANT_APPS` in `AR/settings/base.py` if unsure.*

Always read `claims/v1/views/claim_record_api.py` as the reference before writing a new endpoint.

## Import Paths

```python
# Views
from common.views import BaseARView          # needs client + project context
from common.views import BaseARClientView    # needs client context only (no project)
from rest_framework.generics import GenericAPIView

# Response/Exception
from EPP.custom.custom_api_response import CustomResponse
from EPP.custom.custom_api_exception import CustomException

# Permissions — resource PKs for required_resources
from EPP.product_config.permission_config import (
    ar_agent_resource_pk,
    ar_auditor_resource_pk,
    team_lead_resource_pk,
)

# OpenAPI
from drf_spectacular.utils import extend_schema

# Serializer base classes
from core.utils.serializers.base import CustomSerializer        # Wraps ValidationError → CustomException
from core.utils.serializers.base import CustomModelSerializer   # Wraps ValidationError → CustomException
from core.utils.serializers.camel_case import CamelCaseSerializer  # auto camelCase→snake_case for query params

# Pagination (Custom paginators live in core/utils/pagination.py)
from core.utils.pagination import CustomLimitOffsetPagination

# Filtering
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter, SearchFilter
```

## BaseARView vs BaseARClientView

- **`BaseARView`** — use for endpoints that operate within a project/tenant context (most endpoints). Requires `X-PROJECT-ID` and `X-PROJECT-TYPE` headers. Exposes `request.project` and `request.tenant`.
- **`BaseARClientView`** — use for endpoints that only need client context (e.g., listing projects, client-level settings). No project/tenant resolution.

## List View Pattern (Pagination + Filtering)

**Crucial Architecture Rule:** Keep DRF constructs (`filter_queryset`, `paginator`, `serializers`) OUT of the Service layer. The Service should remain transport-agnostic and return a `QuerySet` or object list, NOT a dictionary.

```python
from rest_framework import status


class MyListAPIView(BaseARView, GenericAPIView):
    """Docstring required."""

    service = MyService
    filter_serializer = MyFilterSerializer       # validates query params
    list_serializer = MyListSerializer           # response serializer
    required_resources = [ar_agent_resource_pk]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = SEARCH_FIELDS                # from <app>/v1/filters/
    ordering_fields = ORDERING_FIELDS
    filterset_class = MyFilterSet                # from <app>/v1/filters/
    pagination_class = CustomLimitOffsetPagination

    @extend_schema(request=MyFilterSerializer, responses=MyListSerializer)
    def get(self, request, *args, **kwargs):
        # 1. Validate Query Params
        filter_serializer = self.filter_serializer(data=request.query_params)
        filter_serializer.is_valid(raise_exception=True)

        # 2. Get Data via Service (Returns a QuerySet, NOT a dict)
        queryset = self.service.get_list_data(
            user_id=request.user.id,
            filters=filter_serializer.validated_data
        )

        # 3. Apply DRF Filters & Paginate
        filtered_queryset = self.filter_queryset(queryset)
        page = self.paginate_queryset(filtered_queryset)

        # 4. Serialize & Wrap Response
        serializer = self.list_serializer(page, many=True)
        paginated_data = self.get_paginated_response(serializer.data).data

        return CustomResponse(data=paginated_data, status=status.HTTP_200_OK)
```

## Serializer Base Class Choices

| Use Case | Base Class | Why |
|----------|-----------|-----|
| PATCH/update input | `serializers.Serializer` or `ModelSerializer` | All fields `required=False` |
| Response (GET) | `serializers.ModelSerializer` | Auto-maps model fields, nested serializers |
| Filter/query params | `CamelCaseSerializer` | Auto-converts camelCase query params to snake_case |
| Input with error formatting | `CustomSerializer` | Wraps `ValidationError` into `CustomException` automatically |
| Response with error formatting | `CustomModelSerializer` | Same wrapping for ModelSerializer |

**Query Parameter Edge Case (Arrays):** `CamelCaseSerializer` is required for query params, but remember that `request.query_params` is a `QueryDict`. If you accept array parameters (e.g., `?status=OPEN&status=CLOSED`), calling `.dict()` on it will drop all but the last value. Extract multi-value keys using `.getlist('status')` before passing data to the serializer if necessary.

## SerializerMethodField — N+1 Rules

`SerializerMethodField` runs once **per instance** during serialization. Any DB access inside `get_<field>` is a guaranteed N+1 on list endpoints.

**NEVER do this in `get_<field>`:**

```python
# ❌ N+1 — fires one query per row
class ClaimSerializer(serializers.ModelSerializer):
    note_count = serializers.SerializerMethodField()
    latest_note = serializers.SerializerMethodField()
    has_followups = serializers.SerializerMethodField()

    def get_note_count(self, obj):
        return obj.notes.count()                    # COUNT(*) per row

    def get_latest_note(self, obj):
        return obj.notes.order_by("-created_at").first()  # SELECT per row

    def get_has_followups(self, obj):
        return obj.followups.filter(resolved=False).exists()  # SELECT per row
```

**Fix order — try in this sequence:**

### 1. Annotate in the queryset (preferred for aggregates / booleans)

Push the computation into the SQL. The serializer field becomes a plain field, no method needed.

```python
# repository
queryset.annotate(
    note_count=Count("notes"),
    has_followups=Exists(Followup.objects.filter(claim=OuterRef("pk"), resolved=False)),
)

# serializer
class ClaimSerializer(serializers.ModelSerializer):
    note_count = serializers.IntegerField(read_only=True)
    has_followups = serializers.BooleanField(read_only=True)
```

Use `Count`, `Sum`, `Avg`, `Max`, `Min`, `Exists`, `Subquery`, `Case/When` — anything ORM-expressible.

### 2. Prefetch when you need full related rows

If you actually need fields off the related object (not just a count), prefetch it once and access via the cached relation. `obj.notes.all()` becomes free after a `prefetch_related("notes")`.

```python
# repository
queryset.prefetch_related(
    Prefetch("notes", queryset=Note.objects.order_by("-created_at"), to_attr="ordered_notes"),
)

# serializer
def get_latest_note(self, obj):
    return obj.ordered_notes[0].text if obj.ordered_notes else None  # no DB hit
```

Always slice prefetched results in Python (`obj.ordered_notes[:5]`); calling `.filter()` or `.order_by()` on the prefetched manager **breaks the cache** and re-queries.

### 3. Compute in the service before serialization

For values that depend on cross-row state, cached data, or business logic that's hard to express in SQL, compute once in the service, attach to each instance (or pass a parallel dict via context), and read in the serializer.

```python
# service
ids = [c.id for c in claims]
followup_counts = dict(Followup.objects.filter(claim_id__in=ids).values_list("claim_id").annotate(c=Count("id")))
for claim in claims:
    claim.followup_count = followup_counts.get(claim.id, 0)

# serializer
class ClaimSerializer(serializers.ModelSerializer):
    followup_count = serializers.IntegerField(read_only=True)
```

### Allowed reads inside `get_<field>`

- Plain attribute access (`obj.field`, `obj.fk.field`) where the FK is `select_related`'d.
- Iterating an already-prefetched relation (`obj.notes.all()` after `prefetch_related("notes")`).
- Pure-Python computation on the instance (no ORM).

If you find yourself writing `obj.<related>.count()`, `obj.<related>.filter(...)`, `obj.<related>.first()`, or `Model.objects.filter(...)` inside a serializer method, stop and pick fix #1, #2, or #3.

## URL Wiring Chain

```text
AR/urls.py
├── "api/v1/" → EPP/v1/urls.py          (Shared apps: users, clients, projects)
├── ""        → core/urls.py
│             └── "api/v1/" → core/v1/urls.py  (Tenant-scoped apps)
│                 ├── "claims/"       → claims/urls.py → claims/v1/urls.py
│                 ├── "ar/claims/"    → ar_ingestion/v1/urls.py
│                 ├── "rules-engine/" → rules_engine/v1/urls.py
│                 ├── "ar/users/"     → user_management/urls.py
│                 ├── "ar/sampling/"  → sampling/v1/urls.py
│                 ├── ""             → ar_common/v1/urls.py
│                 └── "project-setup/" → project_setup/v1/urls.py
└── "api/v1/schema" → Swagger/ReDoc
```

## Swagger / OpenAPI Docs

Every view method must have `@extend_schema()`. There are two patterns:

**1. Inline (simple endpoints)** — pass serializers directly on the decorator:

```python
@extend_schema(request=ClaimRecordUpdateSerializer, responses=ClaimRecordSerializer)
def patch(self, request, claim_id, *args, **kwargs):
```

**2. Extracted schema dict (complex endpoints)** — when you need custom `OpenApiParameter` lists, extract into `<app>/v1/views/swagger_schemas/<schema_name>.py`:

```python
# ar_ingestion/v1/views/swagger_schemas/ar_claims_files_metadata.py
from drf_spectacular.utils import OpenApiParameter

ar_claims_files_metadata_get_schema = dict(
    summary="Retrieve AR Claims File Metadata List",
    description="Retrieve a paginated list of Claim Files Metadata",
    parameters=[
        OpenApiParameter(name="search", type=str, location=OpenApiParameter.QUERY),
    ],
)
```

Then spread it on the view: `@extend_schema(**ar_claims_files_metadata_get_schema)`

**Reusable OpenAPI parameters** live in `core/utils/ar_open_api_params.py`:
- `AR_OPEN_API_PARAMETERS` — standard header params (`X-CLIENT-ID`, `X-PROJECT-ID`, `X-PROJECT-TYPE`)
- `AR_OPEN_API_PAGINATION_PARAMETERS` — `take`/`skip` pagination params

## Detail/Update View Pattern (PATCH)

```python
from rest_framework import status


class MyDetailAPIView(BaseARView, GenericAPIView):
    """Docstring required."""

    service = MyService
    update_serializer = MyUpdateSerializer       # input (PATCH)
    detail_serializer = MyDetailSerializer       # response (GET/PATCH)
    required_resources = [ar_agent_resource_pk]

    @extend_schema(request=MyUpdateSerializer, responses=MyDetailSerializer)
    def patch(self, request, entity_id, *args, **kwargs):
        # 1. Validate Input
        serializer = self.update_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # 2. Service: Validate State + Apply Update
        entity = self.service.validate(entity_id=entity_id, user_id=request.user.id)
        updated_entity = self.service.update(
            entity=entity,
            update_data=serializer.validated_data,
            user=request.user,
        )

        # 3. Serialize & Respond
        response_serializer = self.detail_serializer(updated_entity)
        return CustomResponse(data=response_serializer.data, status=status.HTTP_200_OK)

    @extend_schema(responses=MyDetailSerializer)
    def get(self, request, entity_id, *args, **kwargs):
        entity = self.service.get_detail(entity_id=entity_id, user_id=request.user.id)
        serializer = self.detail_serializer(entity)
        return CustomResponse(data=serializer.data, status=status.HTTP_200_OK)
```

## Filters

Place filter classes in `<app>/v1/filters/`:

```python
# <app>/v1/filters/<entity>_filter.py
import django_filters

from claims.models import ClaimRecord


class ClaimRecordFilterSet(django_filters.FilterSet):
    """FilterSet for ClaimRecord list endpoint."""

    claim_number = django_filters.CharFilter(field_name="claim__claim_number", lookup_expr="exact")
    state = django_filters.NumberFilter(field_name="state_id")
    assigned_to = django_filters.NumberFilter(field_name="assigned_to_id")
    date_from = django_filters.DateFilter(field_name="claim__date_of_service", lookup_expr="gte")
    date_to = django_filters.DateFilter(field_name="claim__date_of_service", lookup_expr="lte")

    class Meta:
        model = ClaimRecord
        fields = []  # all fields defined explicitly above
```

Search and ordering fields go in the same filters directory or file:

```python
# <app>/v1/filters/<entity>_fields.py
SEARCH_FIELDS = [
    "claim__claim_number",
    "claim__patient_name",
]

ORDERING_FIELDS = [
    "claim__charges",
    "claim__date_of_service",
    "state__name",
    "created_at",
]
```

Wire into the view via `filterset_class`, `search_fields`, and `ordering_fields` (see List View Pattern above).

## After Writing Code

1. **Run `pre-commit`** after every code change to catch lint/format issues immediately. Fix any failures before presenting results.
2. **Run `/review-code --staged`** to self-review for bugs, security gaps, missing audit fields, N+1 queries, and convention violations before creating a PR. This catches issues that linters miss (cross-client access, missing `created_by`, duplicate validation gaps, etc.).
