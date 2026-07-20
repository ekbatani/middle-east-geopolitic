# Middle East Geopolitical Intelligence Platform

A planned Python and Hermes-based intelligence platform for collecting, structuring, verifying, analyzing, and reporting geopolitical developments across the Middle East.

The project is designed as a source-driven analytical system rather than a general news chatbot. It will model countries, governments, armed forces, political organizations, non-state actors, conflicts, bilateral relationships, risk indicators, scenarios, evidence, investigations, and forecasts.

## Documentation

1. [Project idea and product specification](docs/01-project-idea.md)
2. [Implementation design](docs/02-implementation-design.md)

## Planned architecture

- **Hermes:** conversational interaction, reports, monitoring, alerts, and investigation commands
- **FastAPI:** authenticated and audited intelligence API
- **PostgreSQL + pgvector:** authoritative structured data, history, and retrieval
- **Celery + Redis:** collection and analytical background jobs
- **MinIO/S3:** raw documents and generated report artifacts
- **LLMs:** structured extraction, evidence comparison, bounded analysis, and report drafting
- **Rules and analyst approval:** verification, scoring, correction, and accountability

## Initial delivery sequence

1. Documentation and architectural standards
2. Python project and local infrastructure
3. Actor, source, document, claim, evidence, and event foundation
4. Automated collection and extraction
5. Relationships, indicators, and explainable risk scoring
6. Scenarios, reporting, and forecast audits
7. Hermes tools, monitoring, and alerts

## Current status

Phase 0 is complete: the Python package (`uv`, Python 3.13), FastAPI/Celery/CLI app skeletons, the shared kernel (config, logging, IDs, security, errors), a Docker Compose stack (Postgres/pgvector, Redis, MinIO, Prometheus, Grafana), an empty Alembic scaffold, and CI (Ruff, mypy, pytest) are in place and passing. No domain models or business logic exist yet — that starts with Phase 1 (actor, source, document, claim, evidence, and event modules).

### Local development

```
uv sync
cp .env.example .env
make dev       # FastAPI on http://localhost:8000
make worker    # Celery worker
make beat      # Celery beat
make test
make lint
make typecheck
make compose-up   # full stack via Docker Compose
```
