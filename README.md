# Middle East Geopolitical Intelligence Platform

A source-driven intelligence platform for collecting, structuring, verifying, analysing, and reporting geopolitical developments across the Middle East.

The platform is built for evidence-led analysis rather than open-ended news chat. It maintains auditable records for actors, sources, documents, claims, evidence, events, relationships, indicators, risks, scenarios, investigations, forecasts, analyst assessments, model reviews, and imagery evidence.

## Documentation

1. [Project idea and product specification](docs/01-project-idea.md)
2. [Implementation design](docs/02-implementation-design.md)
3. [Deployment and operations guide](docs/03-deployment-and-operations.md)
4. [API reference](docs/api.md)
5. [Data model guide](docs/data-model.md)
6. [Risk methodology](docs/risk-methodology.md)

## Architecture

- **Celery + Redis:** collection and analytical background jobs
- **MinIO/S3:** raw documents and generated report artifacts
- **LLMs:** structured extraction, evidence comparison, bounded analysis, and report drafting
- **Rules and analyst approval:** verification, scoring, correction, and accountability

## Current status

Phases 0–6 are complete:

- **Phase 0:** the Python package (`uv`, Python 3.13), FastAPI/Celery/CLI app skeletons, the shared kernel (config, logging, IDs, security, errors), a Docker Compose stack (Postgres/pgvector, Redis, MinIO, Prometheus, Grafana), an empty Alembic scaffold, and CI (Ruff, mypy, pytest).
- **Phase 1:** actor, source, document, claim, evidence, and event modules; authentication and scoped API keys; manual source submission; raw object storage; basic read APIs; audit logging.
- **Phase 2:** RSS/HTTP collectors and source registry; parsing, language detection, and translation; deduplication; LLM claim/event extraction; entity resolution; analyst review queues.
- **Phase 3:** relationship model and observation history; indicator definitions and observations; a deterministic risk-scoring engine with bounded LLM adjustment (`RiskEngine`); risk history and explanation APIs; country-brief and relationship-comparison endpoints.
- **Phase 4:** scenario register and update workflow with sibling-family consistency checks (`ScenarioEngine`); forecast issuance and Brier-score outcome auditing (`ForecastAuditService`); daily/weekly/country/conflict report generation with LLM-optional drafting, Markdown rendering, and an approve/publish workflow (`ReportGenerator`); scenario, forecast, and report APIs; scheduled scenario-update and report-generation worker tasks.
- **Phase 5:** investigation workflow and monitors/alerts engine with authenticated API endpoints. It supports read-only intelligence queries, investigations and report generation, controlled source/note/assessment/imagery/monitor submission, and verified approval actions.
- **Phase 6:** graph analytics and geospatial views; forecast-calibration dashboards; analyst disagreement tracking; multi-model review; and imagery-evidence ingestion and analysis.

See the [implementation design](docs/02-implementation-design.md) for the complete architecture, data model, API boundaries, and delivery plan.

### Local development

```bash
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

Run database migrations before using a fresh local stack:

```bash
make migrate
```

## Quality checks

```bash
make test
make lint
make typecheck
```

