# Migrations

Alembic migrations for the platform's PostgreSQL schema.

Domain modules register their SQLAlchemy models against
`mei.infrastructure.database.base.Base`; import the model module in
`env.py` so `alembic revision --autogenerate` can see it.

```
make migrate            # apply migrations
uv run alembic revision --autogenerate -m "add actors table"
```

No versions exist yet — the first migration lands with Phase 1 (actor,
source, document, claim, evidence, and event tables).
