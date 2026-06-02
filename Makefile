# Student Management — developer task runner.
# Local commands run through `uv`; container commands use docker compose.

.DEFAULT_GOAL := help
# Most targets are not files.
.PHONY: help install run shell migrate migrations superuser \
        test lint format typecheck check \
        celery clean \
        docker-build up down logs ps docker-shell docker-migrate

# ---- local (uv) ----------------------------------------------------------

help: ## Show this help
	@grep -hE '^[a-zA-Z0-9_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| sort \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-16s\033[0m %s\n", $$1, $$2}'

install: ## Sync the virtualenv from uv.lock (incl. dev tools) + pre-commit hooks
	uv sync
	uv run pre-commit install

run: ## Run the dev server on :8000
	uv run python manage.py runserver 0.0.0.0:8000

shell: ## Open the Django shell
	uv run python manage.py shell

migrations: ## Create migrations from model changes
	uv run python manage.py makemigrations

migrate: ## Apply database migrations
	uv run python manage.py migrate

superuser: ## Create a Django superuser (interactive)
	uv run python manage.py createsuperuser

celery: ## Run a Celery worker
	uv run celery -A config worker -l info

# ---- quality -------------------------------------------------------------

test: ## Run the test suite
	uv run pytest student_management/tests/ -q

lint: ## Lint with ruff
	uv run ruff check .

format: ## Auto-format with ruff
	uv run ruff format .

typecheck: ## Static type-check with mypy
	uv run mypy .

check: ## Run all pre-commit hooks on every file (ruff/format/mypy + basics)
	uv run pre-commit run --all-files

# ---- docker compose ------------------------------------------------------

docker-build: ## Build the docker images
	docker compose build

up: ## Start the stack (web + worker + db + redis) in the background
	docker compose up


down: ## Stop the stack
	docker compose down

logs: ## Tail logs from all services
	docker compose logs -f

ps: ## Show running services
	docker compose ps

docker-shell: ## Open a shell in the running web container
	docker compose exec web bash

docker-migrate: ## Apply migrations inside the web container
	docker compose exec web python manage.py migrate

# ---- housekeeping --------------------------------------------------------

clean: ## Remove Python caches and build artifacts
	find . -type d -name '__pycache__' -prune -exec rm -rf {} +
	find . -type d -name '.pytest_cache' -prune -exec rm -rf {} +
	find . -type d -name '.ruff_cache' -prune -exec rm -rf {} +
	find . -type d -name '.mypy_cache' -prune -exec rm -rf {} +
	find . -type f -name '*.py[co]' -delete
