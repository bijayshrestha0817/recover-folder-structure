---
name: test-generator
description: Generates pytest test files following project conventions — class-based tests with real DB fixtures, multi-tenant context, permission checks, and Arrange-Act-Assert pattern. Use when asked to write, generate, or scaffold tests for a view or endpoint.
user-invokable: true
---

# Test Generator

CLAUDE.md (always in context) covers testing rules and strict boundaries. This skill provides the **exact patterns and fixtures** needed to generate test files.

## Step 1: Identify the Target

Read the view class being tested to extract:

1. **View class name and HTTP methods** (get/post/patch/delete)
2. **URL name** — from the app's `v1/urls.py` (e.g., `claims:claim-record-api-view-all`)
3. **`required_resources`** — which resource PKs are needed for permission
4. **Serializer** — what fields the response returns (for assertions)
5. **Service** — what validations and business rules exist (for error cases)

## Step 2: Determine Test Scenarios

Every endpoint needs these test categories. Skip any that don't apply:

| Category | When to include |
|----------|----------------|
| **Success** | Always — happy path for each HTTP method |
| **Permission denial** | Always — test with unauthorized and wrong-resource clients |
| **Validation error** | If the endpoint accepts input (POST/PATCH) |
| **Invalid state** | If the service validates entity state before mutation |
| **Not found** | If the endpoint takes an ID parameter |
| **List/pagination** | If it's a list endpoint with `CustomLimitOffsetPagination` |
| **Filtering** | If the view has `filterset_class` or `search_fields` |
| **Ordering** | If the view has `ordering_fields` |

## Step 3: Generate the Test File

### File Location and Naming

```
<app>/tests/test_<feature>.py
```

Match the view file name: `claim_record_api.py` → `test_claim_record_api.py`

### Imports Block

```python
import pytest
from django.urls import reverse
from django_tenants.utils import tenant_context
from rest_framework import status

from EPP.product_config.permission_config import (
    ar_agent_resource_pk,
    ar_auditor_resource_pk,
    team_lead_resource_pk,
)
from EPP.tests.utils import generate_domain_headers
```

Add model imports only if asserting DB state directly.

### Test Class Structure

```python
@pytest.mark.django_db
class Test<ViewClassName>:
    """Tests for <ViewClassName>."""

    url = reverse("<app>:<url-name>")  # or build in setup if URL has params

    @pytest.fixture(autouse=True)
    def setup(self, client, project, tenant, claim_records, resource_api_client):
        """Set up test data and API clients."""
        self.headers = generate_domain_headers(client=client, project_id=project.id)
        self.client = client
        self.project = project
        self.tenant = tenant
        self.claim_records = claim_records

        # Create API clients matching view's required_resources
        self.team_lead_api_client, self.team_lead_user = resource_api_client(
            team_lead_resource_pk, "team lead"
        )
        self.agent_api_client, self.agent_user = resource_api_client(
            ar_agent_resource_pk, "agent"
        )

    # --- Success ---

    def test_<method>_success(self):
        """Test successful <method> request."""
        response = self.agent_lead_api_client.<method>(self.url, **self.headers)

        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert data["success"] is True

    # --- Permission denial ---

    def test_<method>_unauthorized(self, unauthorized_api_client):
        """Test unauthenticated request returns 401."""
        response = unauthorized_api_client.<method>(self.url, **self.headers)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_<method>_forbidden_wrong_resource(self, resource_api_client):
        """Test user with wrong resource permission returns 403."""
        wrong_client, _ = resource_api_client(ar_auditor_resource_pk, "wrong resource")

        response = wrong_client.<method>(self.url, **self.headers)

        assert response.status_code == status.HTTP_403_FORBIDDEN
```

### URL Patterns

```python
# Static URL (list endpoints)
url = reverse("claims:claim-record-api-view-all")

# Dynamic URL (detail endpoints) — build in setup or per-test
def setup(self, ...):
    self.url = reverse("claims:claim-record-detail", kwargs={"claim_id": self.claim_records[0].id})

# Or use f-string for simple cases
url = f"/api/v1/claims/{claim_record.id}/"
```

## Test Pattern Templates

### GET List — Success + Pagination + Filtering

```python
def test_get_list_success(self):
    """Test list retrieval returns all records."""
    response = self.agent_lead_api_client.get(self.url, **self.headers)

    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert data["success"] is True
    assert data["data"]["pageDetails"]["totalRecords"] == len(self.claim_records)

def test_get_list_pagination(self):
    """Test pagination with take/skip."""
    paginated_url = f"{self.url}?take=2&skip=2"

    response = self.agent_lead_api_client.get(paginated_url, **self.headers)

    assert response.status_code == status.HTTP_200_OK

    page_details = response.json()["data"]["pageDetails"]
    assert page_details["currentPage"] == 2
    assert page_details["recordsPerPage"] == 2
    assert len(response.json()["data"]["results"]) == 2

def test_get_list_filter_by_claim_number(self):
    """Test filtering by claimNumber."""
    first_claim = self.claim_records[0].claim
    filter_url = f"{self.url}?claimNumber={first_claim.claim_number}"

    response = self.agent_lead_api_client.get(filter_url, **self.headers)

    assert response.status_code == status.HTTP_200_OK

    results = response.json()["data"]["results"]
    assert len(results) == 1
    assert results[0]["claim"]["claimNumber"] == first_claim.claim_number

def test_get_list_ordering(self):
    """Test ordering by charges descending."""
    ordering_url = f"{self.url}?ordering=-claim__charges"

    response = self.agent_lead_api_client.get(ordering_url, **self.headers)

    assert response.status_code == status.HTTP_200_OK

    results = response.json()["data"]["results"]
    charges = [r["claim"]["charges"] for r in results]
    assert charges == sorted(charges, reverse=True)

def test_get_list_search(self):
    """Test search by claim number."""
    first_claim = self.claim_records[0].claim
    search_url = f"{self.url}?search={first_claim.claim_number}"

    response = self.agent_lead_api_client.get(search_url, **self.headers)

    assert response.status_code == status.HTTP_200_OK

    results = response.json()["data"]["results"]
    assert len(results) == 1
```

### PATCH — Success + Validation + DB State

```python
def test_patch_success(self):
    """Test successful update."""
    claim_record = self.claim_records[0]
    url = f"/api/v1/claims/{claim_record.id}/"
    payload = {"fieldName": "new_value"}

    with tenant_context(self.tenant):
        claim_record.assigned_to = self.agent_user
        claim_record.save()

    response = self.agent_api_client.patch(url, data=payload, format="json", **self.headers)

    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert data["success"] is True

    # Verify DB state
    with tenant_context(self.tenant):
        claim_record.refresh_from_db()
        assert claim_record.field_name == "new_value"

def test_patch_validation_error(self):
    """Test validation error returns 400 with error details."""
    claim_record = self.claim_records[0]
    url = f"/api/v1/claims/{claim_record.id}/"
    invalid_payload = {"fieldName": "invalid_value"}

    response = self.agent_api_client.patch(url, data=invalid_payload, format="json", **self.headers)

    assert response.status_code == status.HTTP_400_BAD_REQUEST

    data = response.json()
    assert data["success"] is False
    assert "errors" in data
```

### POST — Create + Validation

```python
def test_post_success(self):
    """Test successful creation."""
    payload = {
        "role": "agent",
        "content": "Test content",
    }

    response = self.agent_api_client.post(self.url, data=payload, format="json", **self.headers)

    assert response.status_code == status.HTTP_201_CREATED

    data = response.json()
    assert data["success"] is True
    assert data["data"]["content"] == payload["content"]
```

### Not Found

```python
def test_get_not_found(self):
    """Test non-existent ID returns 404."""
    url = f"/api/v1/claims/999999/"

    response = self.agent_api_client.get(url, **self.headers)

    assert response.status_code == status.HTTP_404_NOT_FOUND

    data = response.json()
    assert data["success"] is False
```

### Invalid State Transition

```python
def test_patch_invalid_state(self, generate_claim_records_with_state):
    """Test update on claim in wrong state returns 400."""
    wrong_state_claims = generate_claim_records_with_state(ingestion_unallocated_pk)
    claim_record = wrong_state_claims[0]
    url = f"/api/v1/claims/{claim_record.id}/"
    payload = {"fieldName": "value"}

    with tenant_context(self.tenant):
        claim_record.assigned_to = self.agent_user
        claim_record.save()

    response = self.agent_api_client.patch(url, data=payload, format="json", **self.headers)

    assert response.status_code == status.HTTP_400_BAD_REQUEST
```

## Fixture Reference

### Available Fixtures (from root conftest.py)

| Fixture | Type | What it provides |
|---------|------|-----------------|
| `client` | Object | `Client` instance |
| `project` | Object | `Project` instance linked to client |
| `tenant` | Object | Tenant with cloned schema |
| `role` / `roles` | Object/List | Role records |
| `regular_user` | Object | Basic authenticated user |
| `agent_user` | Object | User with agent resource |
| `auditor_user` | Object | User with auditor resource |
| `agent_lead_user` | Object | User with agent lead resource |
| `auditor_lead_user` | Object | User with auditor lead resource |
| `api_client` | APIClient | Authenticated as regular_user |
| `agent_api_client` | APIClient | Authenticated as agent_user |
| `auditor_api_client` | APIClient | Authenticated as auditor_user |
| `unauthorized_api_client` | APIClient | Not authenticated |
| `resource_api_client` | Factory | `(resource_pk, name) → (APIClient, User)` |
| `user_with_resource` | Factory | `(resource_pk, name) → User` |
| `claim_state` | Object | ClaimState records (bulk created) |
| `claim_action` | Object | ClaimAction records |
| `claim_status` | Object | ClaimStatus records |
| `claim_disposition` | Object | ClaimDisposition records |
| `claim_records` | List | 20 ClaimRecords with full related data |
| `generate_claim_records_with_state` | Factory | `(state_pk) → List[ClaimRecord]` |
| `payers` | List | Payer records |
| `financial_classes` | List | FinancialClass records |
| `common_resources` | QuerySet | All Resource records |

### Multi-Tenant Context

```python
# Wrap DB reads/writes in tenant_context when outside of an API request
with tenant_context(self.tenant):
    claim_record.refresh_from_db()
    assert claim_record.state_id == expected_state_pk

# API requests auto-resolve tenant via headers — no wrapper needed
response = self.agent_api_client.get(self.url, **self.headers)
```

### Domain Headers

```python
from EPP.tests.utils import generate_domain_headers

# Standard headers (client + project)
self.headers = generate_domain_headers(client=client, project_id=project.id)

# Client-only headers (for BaseARClientView endpoints)
self.headers = generate_domain_headers(client=client)
```

## Rules

1. **Real DB only** — never use `mock`, `patch`, or `MagicMock`. All tests hit the real database with `@pytest.mark.django_db`.
2. **Class-based** — one test class per view class. Use `autouse=True` setup fixture.
3. **Arrange-Act-Assert** — clear separation. Arrange in setup or test body, act with API call, assert response + DB state.
4. **CamelCase in assertions** — response JSON uses camelCase (`claimNumber`, `assignedTo`). Python fixtures use snake_case.
5. **Tenant context for direct DB access** — wrap `refresh_from_db()`, `objects.get()`, and `save()` in `tenant_context(self.tenant)` for tenant-scoped models. API requests resolve tenant automatically via headers.
6. **Use `format="json"` for POST/PATCH** — always pass `format="json"` when sending JSON payloads.
7. **Assert both response and DB state** — for mutations (POST/PATCH/DELETE), assert the response status/body AND verify the database was actually changed.
8. **Use existing fixtures** — check the fixture reference table before creating new fixtures. Use `resource_api_client` factory for custom permission combinations.
9. **Match the view's required_resources** — create API clients with the same resource PKs the view declares in `required_resources`.
10. **Run `pre-commit` after writing tests** — always run `pre-commit` after every code change to catch lint/format issues immediately. Fix any failures before presenting results.
