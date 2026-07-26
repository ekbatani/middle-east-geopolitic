# Middle East Geopolitical Intelligence Platform — API Reference

This document describes the FastAPI REST API specifications, authentication scopes, request/response models, and query conventions for the platform.

---

## 1. Core API Conventions

- **Base URL**: `/api/v1`
- **Format**: JSON (`Content-Type: application/json`)
- **Authentication**: Bearer JWT tokens or HTTP `X-API-Key` headers
- **Time Format**: ISO 8601 UTC timestamps (e.g. `2026-07-26T10:00:00Z`)
- **Pagination**: Cursor-based pagination with `limit` and `cursor` parameters
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

---

## 3. Key API Endpoints

### 3.1 Actors & Entities
- `GET /actors`: List actors with optional filters (`actor_type`, `country_actor_id`).
- `GET /actors/{actor_id}`: Retrieve detailed profile, parent entities, aliases, and leadership.
- `GET /actors/{actor_id}/timeline`: Retrieve temporal history of events and relationship changes for an actor.

### 3.2 Sources & Documents
- `GET /sources`: List registered intelligence sources and feeds.
- `POST /sources/submit`: Submit a URL or document for raw archiving and extraction.
- `GET /documents/{document_id}`: Retrieve normalized document text, metadata, and extracted chunks.

### 3.3 Claims & Verification Evidence
- `GET /claims/{claim_id}`: Retrieve claim details, claimant, subject, verification status, and confidence.
- `GET /claims/{claim_id}/evidence`: Retrieve supporting and contradicting document chunks and stance assessments.
- `POST /claims/{claim_id}/assess`: Submit an analyst assessment or stance update for a claim.

### 3.4 Events
- `GET /events`: Query time-bounded events filtered by location, severity, and status.
- `GET /events/{event_id}`: Get complete event details, participating actors, impacts, and evidence bundle.
- `POST /events/{event_id}/approve`: Senior analyst action to approve an event for canonical use.
- `POST /events/{event_id}/reject`: Reject an unverified or duplicate event.

### 3.5 Relationships
- `GET /relationships`: List durable relationships between actor pairs.
- `GET /relationships/{relationship_id}/history`: Retrieve historical relationship observations across diplomatic, military, economic, and tension dimensions.

### 3.6 Risk Engine
- `GET /risks`: Get current risk assessments across active risk categories (e.g. `interstate_war`, `maritime_disruption`).
- `GET /risks/{risk_id}/history`: Retrieve time-series of risk scores, trend analysis, and indicator breakdowns.
- `POST /risks/recalculate`: Trigger a manual recalculation run for specified risk domains.

### 3.7 Scenarios & Simulation
- `GET /scenarios`: Retrieve active scenario registers (e.g. `controlled_deescalation`, `systemic_regional_war`).
- `POST /scenarios/simulate`: Run a non-canonical hypothetical simulation without altering production records.

### 3.8 Intelligence Query & Hermes Operator Endpoints
Purpose-built composite endpoints used by Hermes MCP operator:
- `POST /intelligence/search`: Hybrid full-text + vector search over documents and approved intelligence.
- `POST /intelligence/country-brief`: Generate unified country intelligence assessment.
- `POST /intelligence/relationship-comparison`: Compare bilateral relationships side-by-side across standardized dimensions.
- `POST /intelligence/risk-explanation`: Retrieve detailed indicator-level explanation for risk score changes.
- `POST /intelligence/daily-brief`: Retrieve or generate the executive daily brief.

### 3.9 System Health
- `GET /health/live`: Liveness probe.
- `GET /health/ready`: Readiness probe (database connectivity check).
- `GET /health/dependencies`: Infrastructure status (Postgres, Redis, MinIO).
