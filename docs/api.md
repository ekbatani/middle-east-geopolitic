# Middle East Geopolitical Intelligence Platform — API Reference

This document describes the FastAPI REST API specifications, authentication scopes, request/response models, and query conventions for the platform.

---

## 1. Core API Conventions

- **Base URL**: `/api/v1`
- **Format**: JSON (`Content-Type: application/json`)
- **Authentication**: Bearer JWT tokens (`Authorization: Bearer <token>`) or API keys (`X-API-Key: mei_...`)
- **Time Format**: ISO 8601 UTC timestamps (e.g. `2026-08-13T12:00:00Z`)
- **Pagination**: Cursor-based and offset pagination with `limit` and `cursor` / `offset` parameters
- **Error Responses**: RFC 9457 Problem Details format (`application/problem+json`)

---

## 2. Authentication and Authorization

### Scopes
- `intelligence:read`: Read-only access to entities, events, claims, and reports.
- `sources:submit`: Permission to submit external URLs or raw documents.
- `investigations:create`: Permission to initiate automated event investigations.
- `events:approve`: Senior analyst permission to approve candidate events.
- `claims:assess`: Permission to submit claim stance assessments.
- `risks:recalculate`: Permission to trigger risk calculation runs.
- `scenarios:simulate`: Permission to execute hypothetical scenario simulations.
- `reports:generate`: Permission to generate structured intelligence reports.
- `monitors:manage`: Permission to create and update monitoring alerts.
- `imagery:submit`: Permission to upload imagery evidence artifacts.

---

## 3. Endpoints Overview

### 3.1 Authentication (`/auth`)
- `POST /api/v1/auth/login`: Authenticate analyst and receive JWT access token.
- `GET /api/v1/auth/me`: Get current authenticated user profile and assigned scopes.
- `POST /api/v1/auth/api-keys`: Create scoped API key for programmatic ingestion/access.

### 3.2 Actors & Entities (`/actors`)
- `GET /api/v1/actors`: List actors with optional filters (`actor_type`, `country_actor_id`).
- `GET /api/v1/actors/{actor_id}`: Retrieve detailed profile, parent entities, aliases, and leadership structure.
- `GET /api/v1/actors/{actor_id}/timeline`: Retrieve temporal history of events and relationship changes for an actor.

### 3.3 Sources & Documents (`/sources`, `/documents`)
- `GET /api/v1/sources`: List registered intelligence sources and feeds.
- `POST /api/v1/sources/submit`: Submit a URL or raw document for archiving and processing.
- `GET /api/v1/documents/{document_id}`: Retrieve normalized document text, metadata, and extracted chunks.

### 3.4 Claims & Verification Evidence (`/claims`, `/review`)
- `GET /api/v1/claims/{claim_id}`: Retrieve claim details, claimant, subject, verification status, and confidence.
- `GET /api/v1/claims/{claim_id}/evidence`: Retrieve supporting and contradicting document chunks and stance assessments.
- `POST /api/v1/claims/{claim_id}/assess`: Submit an analyst assessment or stance update for a claim.
- `GET /api/v1/review/queue`: List unreviewed claims and events pending analyst action.

### 3.5 Events (`/events`)
- `GET /api/v1/events`: Query time-bounded events filtered by location, severity, and status.
- `GET /api/v1/events/{event_id}`: Get complete event details, participating actors, impacts, and evidence bundle.
- `POST /api/v1/events/{event_id}/approve`: Senior analyst action to approve an event for canonical use.
- `POST /api/v1/events/{event_id}/reject`: Reject an unverified or duplicate event.

### 3.6 Relationships & Indicators (`/relationships`, `/indicators`)
- `GET /api/v1/relationships`: List durable relationships between actor pairs.
- `GET /api/v1/relationships/{relationship_id}/history`: Retrieve historical relationship observations across diplomatic, military, economic, and tension dimensions.
- `GET /api/v1/indicators`: List indicator definitions.
- `POST /api/v1/indicators/{code}/observations`: Submit an indicator observation value.

### 3.7 Risk Engine (`/risks`)
- `GET /api/v1/risks`: Get current risk assessments across active risk categories (e.g. `interstate_war`, `maritime_disruption`).
- `GET /api/v1/risks/{risk_id}/history`: Retrieve time-series of risk scores, trend analysis, and indicator breakdowns.
- `POST /api/v1/risks/recalculate`: Trigger a manual recalculation run for specified risk domains.

### 3.8 Scenarios & Forecasts (`/scenarios`, `/forecasts`)
- `GET /api/v1/scenarios`: Retrieve active scenario registers.
- `POST /api/v1/scenarios/simulate`: Run a non-canonical hypothetical simulation without altering production records.
- `GET /api/v1/forecasts`: Retrieve active probabilistic predictions.
- `POST /api/v1/forecasts/{id}/audit`: Post-resolution Brier score evaluation.

### 3.9 Reports (`/reports`)
- `GET /api/v1/reports`: List generated executive briefings and reports.
- `GET /api/v1/reports/{report_id}`: Retrieve Markdown content and metadata for a specific report.
- `POST /api/v1/reports/generate`: Request generation of a daily, weekly, country, or conflict brief.

### 3.10 Composite Intelligence Endpoints (`/intelligence`)
- `POST /api/v1/intelligence/search`: Hybrid full-text + vector search over documents and approved intelligence.
- `POST /api/v1/intelligence/country-brief`: Generate unified country intelligence assessment.
- `POST /api/v1/intelligence/relationship-comparison`: Compare bilateral relationships side-by-side across standardized dimensions.
- `POST /api/v1/intelligence/risk-explanation`: Retrieve detailed indicator-level explanation for risk score changes.
- `POST /api/v1/intelligence/daily-brief`: Retrieve or generate the executive daily brief.

### 3.11 Phase 5: Investigations & Monitors (`/investigations`, `/monitors`)
- `GET /api/v1/investigations`: Query ongoing intelligence investigations.
- `POST /api/v1/investigations`: Create a targeted investigation workflow.
- `GET /api/v1/investigations/{id}`: Get investigation state, findings, and attached notes.
- `GET /api/v1/monitors`: List active automated monitors and alert rules.
- `POST /api/v1/monitors`: Register a new indicator or event threshold monitor.

### 3.12 Phase 6: Advanced Analytics & Evidence (`/graph`, `/analyst-assessments`, `/model-reviews`, `/imagery`)
- `GET /api/v1/graph/nodes`: Graph network nodes (actors, events, locations).
- `GET /api/v1/graph/edges`: Relationship and influence edges for network analysis.
- `GET /api/v1/analyst-assessments/disagreements`: Track consensus and disagreements among analysts.
- `GET /api/v1/model-reviews`: Retrieve multi-model LLM review and verification comparison results.
- `GET /api/v1/imagery`: Query submitted imagery evidence items.
- `POST /api/v1/imagery`: Upload satellite or open-source imagery evidence artifact.

### 3.13 System Health (`/health`)
- `GET /health/live`: Liveness probe (`200 OK`).
- `GET /health/ready`: Readiness probe (database connectivity check).
- `GET /health/dependencies`: Detailed infrastructure status (Postgres, Redis, MinIO).
