# Middle East Geopolitical Intelligence Platform

A source-driven intelligence platform for collecting, structuring, verifying, analysing, and reporting geopolitical developments across the Middle East.

The platform is built for evidence-led analysis rather than open-ended news chat. It maintains auditable records for actors, sources, documents, claims, evidence, events, relationships, indicators, risks, scenarios, investigations, forecasts, analyst assessments, model reviews, imagery evidence, and monitoring alerts.

---

## Documentation

1. [Project idea and product specification](docs/01-project-idea.md)
2. [Implementation design](docs/02-implementation-design.md)
3. [Deployment and operations guide](docs/03-deployment-and-operations.md)
4. [API reference](docs/api.md)
5. [Data model guide](docs/data-model.md)
6. [Risk methodology](docs/risk-methodology.md)
7. [Frontend documentation](apps/frontend/README.md)
8. [Database migrations guide](migrations/README.md)

---

## Architecture

- **FastAPI REST API (`apps/api`)**: Asynchronous API server handling intelligence queries, entity management, risk engine execution, report generation, and analyst workflows.
- **Next.js Web Frontend (`apps/frontend`)**: Modern web dashboard providing interactive intelligence interfaces, geospatial mapping, network graph visualization, risk calibration charts, and investigation management.
- **PostgreSQL + pgvector**: Relational persistence, temporal domain modeling (`valid_from` / `valid_to`), hybrid full-text search (`tsvector`), and vector similarity search (`vector(1536)`).
- **Redis**: High-performance key-value caching and session state management.
- **MinIO / S3 Object Storage**: Raw source document storage, generated Markdown/PDF report artifacts, and imagery evidence files.
- **LLMs & Adapters**: Bounded LLM risk adjustment (`[-10, +10]`), structured extraction, multi-model review, and report drafting (OpenAI, OpenRouter, etc.).
- **Deterministic Rules & Analyst Review**: Auditable scoring, verification queues, analyst stance updates, and canonical approval workflows.

---

## Current Status

Phases 0–6 and the web frontend are complete:

- **Phase 0**: Python package setup (`uv`, Python 3.13), FastAPI & CLI skeletons, shared kernel (config, logging, security, errors), Docker Compose stack (Postgres/pgvector, Redis, MinIO), Alembic scaffold, and CI pipeline (Ruff, mypy, pytest).
- **Phase 1**: Actor, source, document, claim, evidence, and event domain modules; Bearer & X-API-Key auth with scoped permissions; manual source submission; raw object storage integration; audit logging.
- **Phase 2**: RSS/HTTP collectors and source policies; HTML parsing, language detection, and translation; document deduplication; LLM claim/event extraction; entity resolution; analyst review queue endpoints.
- **Phase 3**: Relationship model & observation history; indicator definitions and observations; deterministic `RiskEngine` with bounded LLM adjustment; temporal risk history; country-brief and bilateral comparison endpoints.
- **Phase 4**: Scenario register and update workflow with sibling-family consistency checks (`ScenarioEngine`); forecast issuance and Brier-score auditing (`ForecastAuditService`); executive daily/weekly/country/conflict report generation (`ReportGenerator`).
- **Phase 5**: Investigation workflows, active monitors & alerts engine; authenticated query endpoints; controlled source/note/assessment submission; approval actions.
- **Phase 6**: Graph analytics & network topology; geospatial map interfaces; forecast-calibration dashboards; analyst disagreement tracking; multi-model review engine; imagery evidence ingestion and analysis.
- **Web Frontend**: Full Next.js 15 App Router application (`apps/frontend`) connected to the FastAPI backend, enabling visual exploration of intelligence data.

---

## Quickstart & Local Development

### Prerequisites

- [Python 3.13+](https://www.python.org/)
- [`uv`](https://github.com/astral-sh/uv)
- [Node.js 18+](https://nodejs.org/) & `npm`
- [Docker Engine](https://docs.docker.com/engine/install/) & Docker Compose v2+

### 1. Running via Docker Compose (Recommended)

Start the full stack (PostgreSQL + pgvector, FastAPI API, and Next.js Frontend):

```bash
cp .env.example .env
make compose-up
```

- **Web Frontend**: [http://localhost:3003](http://localhost:3003)
- **FastAPI API Server**: [http://localhost:8000](http://localhost:8000)
- **Interactive API Docs (Swagger)**: [http://localhost:8000/docs](http://localhost:8000/docs)

To stop all services:

```bash
make compose-down
```

### 2. Manual Local Development

#### Backend (FastAPI API)

```bash
# Install dependencies
uv sync

# Setup environment
cp .env.example .env

# Apply database migrations
make migrate

# Seed initial database records
make seed

# Start API server (hot reloading)
make dev
```

#### Frontend (Next.js App)

```bash
cd apps/frontend
npm install
npm run dev
```

The dev frontend will be available at [http://localhost:3000](http://localhost:3000).

---

## Quality Checks

Run the verification suite across the codebase:

```bash
make test        # Run pytest suite
make lint        # Run ruff check & format check
make format      # Apply code formatting fixes
make typecheck   # Run mypy type checker
```
