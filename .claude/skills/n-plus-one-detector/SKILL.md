---
name: n-plus-one-detector
description: Scans a specific view or queryset and suggests where to implement select_related or prefetch_related to optimize database performance based on the accessed fields.
user-invokable: true
---

# N+1 Query Detector

CLAUDE.md (always in context) covers the layered architecture and strict boundary rules. This skill provides the **analysis workflow** for detecting and fixing N+1 query issues.

## When to Use

- User asks to check a view, serializer, or repository for N+1 queries
- User asks to optimize database performance for an endpoint
- Reviewing a new or modified queryset that returns related objects

## Step 1: Identify the Target Endpoint

Determine the full request path from URL to database:

1. **View** — find the view class and its HTTP method (get/post/patch/delete)
2. **Service** — trace which service method the view calls
3. **Repository** — trace which repository method the service calls
4. **Serializer** — find both the response serializer and any nested serializers

Read all four files. The N+1 risk lives in the gap between what the **serializer accesses** and what the **repository prefetches**.

## Step 2: Map Serializer Field Access

For the response serializer, classify every field that touches a relationship:

| Access Type | Example | Optimization |
|-------------|---------|--------------|
| Nested serializer (FK/O2O) | `claim = ARClaimSerializer()` | `select_related("claim")` |
| Nested serializer (reverse FK/M2M) | `notes = ClaimNoteSerializer(many=True)` | `prefetch_related("claim_notes")` |
| `source="fk.field"` | `payer_name = CharField(source="payer.payer_name")` | `select_related("payer")` |
| `SerializerMethodField` accessing related obj | `obj.claim.payer.payer_name` | `select_related("claim__payer")` |
| `SerializerMethodField` with queryset | `obj.carc_claim_lines.filter(...)` | `prefetch_related` or annotate at repository |

Build a list of **all relation paths the serializer will trigger**.

## Step 3: Audit the Repository Queryset

Read the repository method and extract:

1. **Current `select_related()` calls** — list all relation paths
2. **Current `prefetch_related()` calls** — list all relation paths, including custom `Prefetch` objects
3. **Annotations/Subqueries** — fields computed at DB level (no N+1 risk)
4. **`only()` / `defer()` calls** — field restrictions

## Step 4: Diff and Report

Compare serializer access (Step 2) against repository optimization (Step 3). Report findings in this format:

```
## N+1 Query Analysis: <ViewClass.method>

### Request Path
View: <app>/v1/views/<file>.py → <ViewClass.method>
Service: <app>/v1/service/<file>.py → <ServiceClass.method>
Repository: <app>/repository/<file>.py → <RepositoryClass.method>
Serializer: <app>/v1/serializers/<file>.py → <SerializerClass>

### Findings

| # | Severity | Relation Path | Accessed By | Fix |
|---|----------|---------------|-------------|-----|
| 1 | HIGH | claim__payer | ARClaimSerializer.payer_name (source) | Add to select_related |
| 2 | MEDIUM | claim_notes | ClaimNoteSerializer (many=True) | Add prefetch_related |
| 3 | LOW | audit_session | SerializerMethodField (conditional) | Add to select_related if frequently accessed |

### Already Optimized
- `claim` — select_related ✓
- `state` — select_related ✓
- `assigned_to` — select_related ✓

### Suggested Fix

<exact code change for the repository method>
```

### Severity Levels

| Level | Meaning |
|-------|---------|
| **HIGH** | Triggered on every item in a list endpoint — guaranteed N+1 |
| **MEDIUM** | Triggered conditionally or on detail endpoints — likely N+1 |
| **LOW** | Triggered rarely or already mitigated by context/annotation |
| **OK** | Already optimized — no action needed |

## Step 5: Check for Anti-Patterns

Flag these additional issues if found:

1. **Query in serializer** — any `objects.filter()`, `.get()`, `.first()`, or `.select_related()` inside a serializer method. Fix: move to repository annotation or `Prefetch`.
2. **Bare queryset in repository** — returning `Model.objects.all()` or `.filter()` without `select_related`/`prefetch_related` when the serializer accesses relationships. Fix: add appropriate prefetch.
3. **Chained select_related missing depth** — `select_related("claim")` when serializer accesses `claim.payer.payer_name`. Fix: use `select_related("claim__payer")`.
4. **prefetch_related without Prefetch object** — using string-based prefetch when a filtered or annotated queryset would reduce data. Fix: use `Prefetch()` with custom queryset.
5. **Annotation opportunity** — `SerializerMethodField` doing simple lookups that could be a single `Subquery` annotation. Fix: annotate at repository level.

## Step 6: Scan SerializerMethodField Bodies (highest-yield check)

`SerializerMethodField` is the single most common N+1 source in this codebase. For each `get_<field>` method on the response serializer (and any nested serializers), scan the body for these red flags:

| Red flag | Why it's N+1 | Fix |
|---|---|---|
| `obj.<related>.count()` | One COUNT per row | `Count(...)` annotation in repository |
| `obj.<related>.exists()` | One SELECT per row | `Exists(...)` annotation |
| `obj.<related>.first()` / `.last()` | One SELECT per row | `Subquery` annotation, or `Prefetch` then `[0]` in Python |
| `obj.<related>.filter(...)` | One SELECT per row | `Prefetch(..., queryset=...)`, slice in Python |
| `obj.<related>.order_by(...).first()` | One SELECT per row | `Subquery` annotation |
| `Model.objects.filter(...)` | One SELECT per row | Repository-level prefetch or annotation |
| `obj.<related>.aggregate(...)` | One aggregation per row | `Sum`/`Avg`/etc. annotation |
| `obj.<related>.all()[:N]` after `prefetch_related` is OK if the prefetch matches |  |  |

If any red flag is hit, classify it as **HIGH** severity for list endpoints and add it to the findings table from Step 4.

Also flag the inverse: `SerializerMethodField` doing **only** plain attribute access (`obj.fk.field`) where the FK is already `select_related`'d — that's fine. Just confirm the FK chain is in `select_related`.

For full patterns (annotate vs prefetch vs compute-in-service), reference `/drf-conventions` → "SerializerMethodField — N+1 Rules".

## Rules

1. **Repository only** — all fixes must go in the repository layer. Never add query logic to serializers or views.
2. **Trace the full path** — don't guess. Read the actual serializer, service, and repository code before reporting.
3. **List vs detail matters** — a missing `select_related` on a list endpoint (N items) is HIGH severity. On a detail endpoint (1 item) it's MEDIUM.
4. **Count queries, not just relations** — a `SerializerMethodField` that runs a queryset inside a loop is worse than a missing `select_related`.
5. **Preserve existing optimizations** — when suggesting fixes, show the full updated `select_related`/`prefetch_related` call including existing relations, not just the new ones.

## Project-Specific Patterns

### Common Relation Chains (claims app)

These are the frequently needed prefetch paths based on the existing codebase:

```python
# ClaimRecord list endpoint — typical select_related
ClaimRecord.objects.select_related(
    "claim",                          # OneToOne → ARClaim
    "claim__payer",                   # ARClaim → Payer
    "claim__financial_class",         # ARClaim → FinancialClass
    "claim__arclaimpayertagging",     # ARClaim → PayerTagging
    "claim__project",                 # ARClaim → Project
    "state",                          # FK → ClaimState
    "claim_status",                   # FK → ClaimStatus
    "claim_disposition",              # FK → ClaimDisposition
    "assigned_to",                    # FK → User
    "agent",                          # FK → User
    "auditor",                        # FK → User
    "last_touched_by",               # FK → User
    "validation_status",             # FK → ValidationStatus
)

# ClaimNote — advanced Prefetch with filtered queryset
ClaimNote.objects.select_related(
    "user", "audit_session", "audit_session__auditor"
).prefetch_related(
    Prefetch(
        "audit_session__auditresponse_set",
        queryset=AuditResponse.objects.filter(...)
            .select_related("question", "question__error_category")
            .prefetch_related("failure_reasons"),
        to_attr="failed_responses",
    )
)

# Service line codes — reverse FK prefetch
queryset.prefetch_related(
    "arclaimmodifiercodetagging_set__modifier_code",
    "arclaimdenialcode_set__denial_code",
    "arclaimcptcodetagging_set__cpt_code",
)
```

### Discover Existing Hotspots Live

Don't rely on a hardcoded list — that rots fast as fixes land. When asked for a codebase-wide audit, run these grep patterns to surface candidates, then trace each one through the Step 1–6 workflow:

```bash
# SerializerMethodField bodies that hit the DB (highest yield)
git grep -nE '\.objects\.(filter|get|first|count|exists|all)\(' -- '*/v1/serializers/*.py'
git grep -nE 'obj\.\w+\.(filter|first|last|count|exists|order_by|aggregate)\(' -- '*/v1/serializers/*.py'

# Repositories returning bare querysets (no select_related/prefetch_related)
git grep -nE 'return \w+\.objects\.(all|filter)\(' -- '*/repository/*.py'

# Bare .get() / .first() in services/repos that should chain select_related
git grep -nE '\.objects\.(get|first)\(' -- '*/repository/*.py' '*/v1/service/*.py'
```

Order findings by blast-radius:

1. **List endpoints first** (any view backed by a paginator) — every issue is multiplied by `page_size`.
2. **Detail endpoints next** — single-row, but accumulates across users.
3. **Background tasks last** — Celery tasks that loop over many rows.

Skip false positives: `obj.related.all()` after a `prefetch_related("related")` is fine; verify against the repository before flagging.
