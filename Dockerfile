FROM python:3.12-slim-bookworm

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never \
    UV_PROJECT_ENVIRONMENT=/.venv \
    PATH="/.venv/bin:$PATH"

# install uv
COPY --from=ghcr.io/astral-sh/uv:0.11.4 /uv /uvx /bin/

COPY pyproject.toml uv.lock /_lock/

RUN --mount=type=cache,target=/root/.cache \
    cd /_lock && \
    uv sync --frozen

# copy project
COPY . /app

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
