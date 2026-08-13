# Database Migrations

Alembic migrations for the platform's PostgreSQL schema.

Domain modules register their SQLAlchemy models against `mei.infrastructure.database.base.Base`; import the model module in `migrations/env.py` so `alembic revision --autogenerate` can see it.

---

## Running Migrations

```bash
# Apply all pending database migrations
make migrate

# Create a new migration revision
uv run alembic revision --autogenerate -m "description of migration"

# Check current revision status
uv run alembic current
```

---

## Migration History

The schema is organized into modular phase migrations:

1. `b43ba5d65f49`: **Phase 1 — Intelligence Foundation** (Actors, Aliases, Sources, Documents, Document Chunks, Claims, Claim Evidence, Events, Event Actors, Event Locations, Event Impacts, Evidence Bundles, API Keys, Audit Logs).
2. `c7a1e9f2b3d4`: **Phase 2 — Collection & Extraction** (Source Feeds, Extraction Run Logs, Entity Resolution Candidates).
3. `e1b2c3d4f5a6`: **Phase 3 — Relationships & Risk Engine** (Relationships, Relationship Observations, Indicator Definitions, Indicator Observations, Risk Assessments).
4. `f4a5b6c7d8e9`: **Phase 4 — Scenarios & Reports** (Scenarios, Scenario Assessments, Forecast Records, Reports).
5. `a5b6c7d8e9f0`: **Phase 5 — Investigations & Monitors** (Investigations, Investigation Notes, Monitors, Monitor Alerts).
6. `b1c2d3e4f5a6`: **Phase 6 — Advanced Analysis & Evidence** (Graph Topology, Analyst Disagreements, Calibration Records, Multi-Model Reviews, Imagery Evidence).
