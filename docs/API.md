# Student Management API — Frontend Integration Guide

> Practical, copy-paste-friendly reference for building the frontend against this API.
> For an always-up-to-date interactive schema, open **`/api/docs/`** (Swagger) or
> **`/api/schema/redoc/`** (ReDoc). Raw OpenAPI JSON: **`/api/schema/`**.

---

## 1. Conventions at a glance

| Topic | Value |
|-------|-------|
| Base URL (local) | `http://localhost:8000` |
| Frontend URL (used in reset links) | `http://localhost:3000` |
| Content type | `application/json` |
| Auth scheme | JWT Bearer — `Authorization: Bearer <access_token>` |
| Versioned routes | prefixed with `/api/v1/` |
| Auth/account routes | top-level (`/auth/...`, `/register/`) — **not** under `/api/v1/` |
| Default page size | 10 |

### CORS
The API allows the configured frontend origin. Send the JWT in the `Authorization`
header (not cookies); no CSRF token is needed for the JWT-authenticated JSON endpoints.

---

## 2. Response shape — READ THIS FIRST

Most endpoints wrap their payload in a **standard envelope**. A few legacy/3rd-party
endpoints return **raw DRF** shapes. Your HTTP client should handle both — Section 6
flags every endpoint that is NOT wrapped.

### 2a. Standard envelope (success)

```json
{
  "data": { "...": "endpoint-specific payload" },
  "message": "Student fetched successfully",
  "success": true,
  "errors": null,
  "code": "success",
  "status": 200
}
```

| Field | Type | Meaning |
|-------|------|---------|
| `data` | object \| array \| null | The actual payload. `null` for delete/empty responses. |
| `message` | string | Human-readable summary (safe to surface as a toast). |
| `success` | boolean | `true` on success, `false` on error. **Branch on this.** |
| `errors` | object \| null | Field-level or detail errors (only on failure). |
| `code` | string | Machine code: `"success"`, or an error code like `"validation_error"`. |
| `status` | number | Mirrors the HTTP status code. |

### 2b. Standard envelope (error)

The same envelope is used for **all** handled errors (validation, 401, 403, 404, 409, 429…):

```json
{
  "data": null,
  "message": "Incorrect current password.",
  "success": false,
  "errors": null,
  "code": "validation_error",
  "status": 400
}
```

When the error is a DRF field-validation error, `errors` carries the field map and
`message` is `"Request failed."`:

```json
{
  "data": null,
  "message": "Request failed.",
  "success": false,
  "errors": { "email": ["This field must be unique."] },
  "code": "invalid",
  "status": 400
}
```

> **Recommended client rule:** treat any response with `success === false` (or HTTP
> status ≥ 400) as an error. Prefer `errors` for inline field messages; fall back to
> `message` for a general toast.

### 2c. Paginated payloads (envelope)

For wrapped list endpoints, the page lives **inside** `data`:

```json
{
  "data": {
    "count": 42,
    "next": "http://localhost:8000/api/v1/students/?page=2",
    "previous": null,
    "results": [ { "id": 1, "name": "...", "...": "..." } ]
  },
  "message": "Student fetched successfully",
  "success": true,
  "errors": null,
  "code": "success",
  "status": 200
}
```

---

## 3. Authentication

### Flow
1. **Login** → `POST /auth/token/` with username + password → returns `access` + `refresh`.
2. Send `Authorization: Bearer <access>` on every protected request.
3. When `access` expires (401) → **refresh** via `POST /auth/token/refresh/`.
4. **Logout** → `POST /auth/logout/` with the `refresh` token (it gets blacklisted).

### Token lifetimes
Uses Simple JWT defaults: **access ≈ 5 min**, **refresh ≈ 24 h**. Build a refresh-on-401
interceptor; once the refresh token expires, force re-login.

> ⚠️ The JWT endpoints (`/auth/token/`, `/auth/token/refresh/`) return **raw Simple JWT
> JSON**, NOT the standard envelope. See Section 6.

---

## 4. Filtering, search, ordering, pagination

Available on the wrapped list endpoints (`/api/v1/students/`, `/api/v1/courses/`) via query params:

| Param | Example | Notes |
|-------|---------|-------|
| `page` | `?page=2` | Page number; page size = 10. |
| `search` | `?search=alice` | Case-insensitive partial match across the endpoint's search fields. |
| `ordering` | `?ordering=name` / `?ordering=-age` | `-` prefix = descending. Only declared fields. |
| filter fields | `?course=3` | Exact-match filters (endpoint-specific). |

Per-endpoint capabilities:

| Endpoint | `search` fields | `ordering` fields | filter fields |
|----------|-----------------|-------------------|---------------|
| `/api/v1/students/` | `name`, `email` | `name`, `age`, `id` | `course` |
| `/api/v1/courses/` | `name` | `name`, `id` | — |

Example: `GET /api/v1/students/?course=3&search=jo&ordering=-age&page=1`

---

## 5. Rate limits (HTTP 429)

| Action | Scope | Limit |
|--------|-------|-------|
| Login (`/auth/token/`) | `login` | 10 / minute |
| Change password | `change_password` | 10 / minute |
| Password reset request & confirm | `password_reset` | 5 / hour |

On exceeding a limit you get the standard error envelope with `status: 429` and a
`Retry-After` header. Surface a "try again later" message.

---

## 6. Endpoint reference

Legend: 🔓 public · 🔑 requires JWT · 👑 requires admin (superuser).
**Env?** = is the response wrapped in the standard envelope (Section 2)?

### Auth & account

| Method | Path | Access | Env? |
|--------|------|--------|------|
| POST | `/auth/token/` | 🔓 | ❌ raw JWT |
| POST | `/auth/token/refresh/` | 🔓 | ❌ raw JWT |
| POST | `/register/` | 🔓 | ✅ |
| GET | `/auth/me/` | 🔑 | ✅ |
| POST | `/auth/logout/` | 🔑 | ✅ |
| PUT | `/auth/change-password/` | 🔑 | ✅ |
| POST | `/auth/reset-password/` | 🔓 | ✅ |
| POST | `/auth/reset-password-confirm/` | 🔓 | ✅ |

#### `POST /auth/token/` — Login
Request:
```json
{ "username": "alice", "password": "secret123" }
```
Response (raw, **no envelope**):
```json
{ "access": "<jwt-access>", "refresh": "<jwt-refresh>" }
```
Errors: `401` `{ "detail": "No active account found with the given credentials" }` (raw).

#### `POST /auth/token/refresh/` — Refresh access token
Request: `{ "refresh": "<jwt-refresh>" }`
Response (raw): `{ "access": "<new-jwt-access>" }`

#### `POST /register/` — Register a normal user
Request:
```json
{ "username": "alice", "email": "alice@example.com", "password": "secret123" }
```
Response `201` (envelope `data`): `{ "username": "alice", "email": "alice@example.com" }`
(`password` is write-only, never returned.)

#### `GET /auth/me/` — Current user
Response `200` (envelope `data`): `{ "id": 1, "username": "alice", "email": "alice@example.com" }`

#### `POST /auth/logout/` — Blacklist refresh token
Request: `{ "refresh": "<jwt-refresh>" }`
Response `200`: envelope, `message: "Successfully logged out."`

#### `PUT /auth/change-password/` — Change password (logged in)
Request:
```json
{ "current_password": "secret123", "new_password": "An0ther$tr0ng1" }
```
Response `200`: envelope, `message: "Password changed successfully."`
Errors `400`: `"Incorrect current password."` / `"You cannot reuse an old password."` /
password-strength validation errors in `errors`.

#### `POST /auth/reset-password/` — Request a reset link
Request: `{ "email": "alice@example.com" }`
Response `200` (always the same, whether or not the email exists — anti-enumeration):
```json
{ "message": "If an account exists for that email, a reset link has been sent.", "success": true, "...": "..." }
```
The email contains a link of the form
`http://localhost:3000/reset-password?uid=<uid>&token=<token>` — the **frontend** owns
that route and posts the values to the confirm endpoint.

#### `POST /auth/reset-password-confirm/` — Set a new password via link
Request:
```json
{ "uid": "<from-link>", "token": "<from-link>", "new_password": "An0ther$tr0ng1" }
```
Response `200`: envelope, `message: "Password reset successfully. Please login."`
Errors `400`: `"Invalid UID."` / `"Invalid or expired token."` / password-strength errors.

---

### Students

| Method | Path | Access | Env? | Purpose |
|--------|------|--------|------|---------|
| GET | `/api/v1/student-list/` | 🔓 | ❌ raw DRF | Public read-only list (paginated). |
| GET | `/api/v1/students/` | 🔑 | ✅ | List (filter/search/order/paginate). |
| POST | `/api/v1/students/` | 🔑 | ✅ | Create a student. |
| GET | `/api/v1/students/{id}/` | 🔑 | ✅ | Retrieve one. |
| PUT | `/api/v1/students/{id}/` | 🔑 | ✅ | Full update. |
| PATCH | `/api/v1/students/{id}/` | 🔑 | ✅ | Partial update. |
| DELETE | `/api/v1/students/{id}/` | 🔑 | ✅ | Delete (`204`, `data: null`). |

**Student object:**
```json
{
  "id": 1,
  "name": "Alice",
  "email": "alice@example.com",
  "age": 21,
  "course": 3,
  "course_name": "Mathematics"
}
```
- `course` — write the Course **id**. `course_name` is read-only (resolved name).
- Create/update request body: `{ "name", "email", "age", "course" }`. `email` is unique.

> ⚠️ `GET /api/v1/student-list/` returns the **raw DRF** page
> `{ "count", "next", "previous", "results": [...] }` directly (no envelope).
> The authenticated `GET /api/v1/students/` wraps that same page inside `data` (Section 2c).

---

### Courses

| Method | Path | Access | Env? | Purpose |
|--------|------|--------|------|---------|
| GET | `/api/v1/courses/` | 🔑 | ✅ | List (search/order/paginate, page size 10). |
| POST | `/api/v1/courses/` | 🔑 | ✅ | Create a course. |
| GET | `/api/v1/courses/all/` | 🔓 | ✅ | **Unpaginated** list for dropdowns. |
| GET | `/api/v1/courses/{id}/` | 🔑 | ✅ | Retrieve one. |
| PUT | `/api/v1/courses/{id}/` | 🔑 | ✅ | Full update. |
| PATCH | `/api/v1/courses/{id}/` | 🔑 | ✅ | Partial update. |
| DELETE | `/api/v1/courses/{id}/` | 🔑 | ✅ | Delete (`204`). |

**Course object:**
```json
{ "id": 3, "name": "Mathematics", "created_at": "2026-06-01T10:00:00Z", "updated_at": "2026-06-01T10:00:00Z" }
```
- Create/update request body: `{ "name" }`. Timestamps are read-only.
- `GET /api/v1/courses/all/` → envelope with `data` as a **plain array** (no pagination):
  ```json
  { "data": [ { "id": 3, "name": "Mathematics", "...": "..." } ], "message": "Dropdown data fetched", "success": true, "...": "..." }
  ```

---

### Admin (superuser management) 👑

All require an authenticated **superuser** (`403` otherwise).

| Method | Path | Access | Env? | Purpose |
|--------|------|--------|------|---------|
| GET | `/api/v1/admin-list/` | 👑 | ❌ raw DRF | List superusers (paginated). |
| POST | `/api/v1/auth/users/` | 👑 | ✅ | Create a superuser. |
| GET | `/api/v1/admin/{id}/` | 👑 | ❌ raw DRF | Retrieve a superuser. |
| PUT/PATCH | `/api/v1/admin/{id}/` | 👑 | ❌ raw DRF | Update a superuser. |
| DELETE | `/api/v1/admin/{id}/` | 👑 | ❌ raw DRF | Delete a superuser. |

**Admin/User object:** `{ "id", "username", "email" }` (`password` is write-only on create).

> ⚠️ Only `POST /api/v1/auth/users/` (create) uses the envelope. The list and
> `/admin/{id}/` detail endpoints return **raw DRF** shapes (raw page for the list,
> bare object for detail).

---

## 7. HTTP status codes you'll see

| Status | When |
|--------|------|
| 200 | Successful GET / update / action. |
| 201 | Resource created. |
| 204 | Deleted (envelope endpoints still send a body with `data: null`). |
| 400 | Validation error (see `errors`). |
| 401 | Missing/expired/invalid token → refresh or re-login. |
| 403 | Authenticated but not allowed (e.g. non-admin hitting admin routes). |
| 404 | Resource not found. |
| 409 | Conflict (e.g. integrity/uniqueness conflict surfaced by the service layer). |
| 429 | Rate limit hit — check `Retry-After`. |

---

## 8. Quick client helper (TypeScript)

```ts
const BASE = "http://localhost:8000";

async function api<T>(path: string, init: RequestInit = {}): Promise<T> {
  const token = localStorage.getItem("access");
  const res = await fetch(`${BASE}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...init.headers,
    },
  });
  const body = await res.json().catch(() => null);

  // Envelope endpoints expose `success`; raw endpoints (JWT, public lists) don't.
  if (!res.ok || (body && body.success === false)) {
    const message = body?.message ?? body?.detail ?? "Request failed";
    throw { status: res.status, message, errors: body?.errors ?? null };
  }
  // Prefer the envelope's `data`; otherwise return the raw body.
  return (body && "data" in body ? body.data : body) as T;
}
```

---

*Generated from the live source (`config/urls.py`, `student_management/v1/`, `core/`,
`custom/`). If an endpoint's behaviour differs from this doc, the interactive schema at
`/api/docs/` is authoritative — please flag the mismatch.*
