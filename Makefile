.PHONY: install dev worker beat migrate seed test lint typecheck format compose-up compose-down

install:
	uv sync

dev:
	uv run uvicorn apps.api.main:app --reload --host 0.0.0.0 --port 8000

worker:
	uv run celery -A apps.worker.celery_app worker --loglevel=INFO

beat:
	uv run celery -A apps.worker.celery_app beat --loglevel=INFO

migrate:
	uv run alembic upgrade head

seed:
	uv run python scripts/seed.py

test:
	uv run pytest

lint:
	uv run ruff check .
	uv run ruff format --check .

format:
	uv run ruff format .
	uv run ruff check --fix .

typecheck:
	uv run mypy .

compose-up:
	docker compose up --build -d

compose-down:
	docker compose down
