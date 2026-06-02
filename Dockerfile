# syntax=docker/dockerfile:1.9

# ---- builder: resolve + install dependencies into an isolated venv ----
FROM python:3.12-slim-bookworm AS builder

# uv: fast, reproducible installs straight from uv.lock
COPY --from=ghcr.io/astral-sh/uv:0.11.4 /uv /uvx /bin/

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never \
    UV_PROJECT_ENVIRONMENT=/opt/venv

WORKDIR /app

# 1) Install ONLY third-party deps (no project, no dev tooling). This layer is
#    cached and rebuilds only when uv.lock / pyproject.toml change — not on every
#    source edit. --no-dev drops ruff/mypy/pytest/pre-commit from the image.
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-install-project --no-dev

# 2) Add the source and install the project itself into the same venv.
COPY . /app
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev


# ---- runtime: slim image with just the venv + app; no uv, no caches, non-root ----
FROM python:3.12-slim-bookworm AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH"

# Run as an unprivileged user.
RUN groupadd --system app && useradd --system --gid app --home-dir /app app

WORKDIR /app

# venv (deps + installed project) lives at /opt/venv — OUTSIDE /app — so the
# compose dev bind-mount (.:/app) never shadows it. Source is copied for
# standalone (no-mount) runs.
COPY --from=builder --chown=app:app /opt/venv /opt/venv
COPY --from=builder --chown=app:app /app /app

USER app

EXPOSE 8000

# Default command; docker-compose overrides it per service (web / worker).
# For production, prefer a WSGI server (e.g. gunicorn) over runserver.
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
