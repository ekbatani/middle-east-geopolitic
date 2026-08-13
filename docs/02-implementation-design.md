# Middle East Geopolitical Intelligence Platform — Implementation Design

## 1. Document purpose

This document defines how to implement the platform described in `01-project-idea.md`.

It covers:

- system architecture;
- service boundaries;
- repository structure;
- technology choices;
- database design;
- ingestion and analysis pipelines;
- risk and scenario engines;
- APIs and tools;
- scheduling and background jobs;
- authentication, authorization, and security;
- observability;
- testing and evaluation;
- deployment;
- phased implementation.

The initial design favors a modular monolith with durable background jobs. It is intentionally simpler than a microservice architecture while keeping domain boundaries explicit enough to split later.

---

## 2. Architectural goals

The implementation must provide:

1. durable and auditable intelligence records;
2. strict separation of raw sources, claims, assessments, and approved facts;
3. time-aware actor and relationship histories;
4. explainable risk scores;
5. repeatable investigations;
6. multilingual source processing;
7. controlled LLM usage;
8. a narrow, secure tool interface;
9. reliable scheduled collection and reporting;
10. simple local and single-server deployment for the MVP.

---

## 3. High-level architecture

```text
┌───────────────────────────────────────────────────────────────┐
│                       Interaction Layer                       │
│                                                               │
│ Dashboard   Telegram   CLI   Web Application                  │
└───────────────────────────────┬───────────────────────────────┘
                                │
                           HTTPS tools
                                │
┌───────────────────────────────▼───────────────────────────────┐
│                         FastAPI API                           │
│                                                               │
│ Auth  Queries  Commands  Investigations  Reports  Job Status │
└───────────────┬──────────────────┬──────────────────┬─────────┘
                │                  │                  │
       Application services   Domain services    Event publisher
                │                  │                  │
┌───────────────▼──────────────────▼──────────────────▼─────────┐
│                 Python Modular Monolith Core                  │
│                                                               │
│ Actors        Sources        Documents       Claims           │
│ Events        Evidence       Relationships   Indicators       │
│ Risks         Scenarios      Reports         Forecast Audit   │
│ Investigations              Notifications                     │
└───────────────┬──────────────────┬──────────────────┬─────────┘
                │                  │                  │
        PostgreSQL/pgvector   MinIO or S3       Redis
                │                                     │
                └──────────────────┬──────────────────┘
                                   │
                          Celery workers and Beat
                                   │
┌──────────────────────────────────▼────────────────────────────┐
│                   Collection and Analysis                     │
│                                                               │
│ RSS/API   HTTP/Browser   Parsing   Translation   Extraction   │
│ Deduplication   Entity resolution   Verification   Scoring    │
└───────────────────────────────────────────────────────────────┘
```

---

## 4. Technology stack

### 4.1 Runtime and package management

- Python 3.13
- `uv` for dependency and virtual-environment management
- `pyproject.toml` as the package definition

### 4.2 API and validation

- FastAPI
- Pydantic v2
- Uvicorn

### 4.3 Persistence

- PostgreSQL 16 or later
- SQLAlchemy 2 async ORM
- Alembic migrations
- pgvector for semantic retrieval
- PostgreSQL full-text search for lexical retrieval

### 4.4 Background processing

- Redis
- Celery
- Celery Beat

Celery is sufficient for the MVP. Temporal can replace or supplement it if investigations later require complex, long-running, resumable orchestration with extensive human-in-the-loop steps.

### 4.5 Source collection

- HTTPX for HTTP clients
- feedparser for RSS and Atom
- Trafilatura for article extraction
- Playwright for browser-required sources
- Beautiful Soup only for source-specific parsing where needed

### 4.6 Data processing

- Polars for bulk tabular transformations
- NetworkX for graph calculations
- RapidFuzz for alias matching
- dateparser for multilingual date parsing where safe

### 4.7 Storage

- MinIO for self-hosted development and deployment
- S3-compatible object storage in production

### 4.8 Quality and testing

- Ruff
- mypy
- pytest
- pytest-asyncio
- testcontainers
- Hypothesis for selected rules and scoring tests

### 4.9 Observability

- structured JSON logging
- OpenTelemetry
- Prometheus
- Grafana
- Sentry as an optional application-error layer

---

## 5. Repository structure

```text
middle-east-geopolitic/
├── README.md
├── pyproject.toml
├── uv.lock
├── .env.example
├── .gitignore
├── Makefile
├── docker-compose.yml
├── Dockerfile
│
├── apps/
│   ├── api/
│   │   ├── main.py
│   │   ├── dependencies.py
│   │   ├── middleware/
│   │   └── routers/
│   │       ├── auth.py
│   │       ├── actors.py
│   │       ├── sources.py
│   │       ├── documents.py
│   │       ├── claims.py
│   │       ├── events.py
│   │       ├── relationships.py
│   │       ├── risks.py
│   │       ├── scenarios.py
│   │       ├── investigations.py
│   │       ├── reports.py
│   │       ├── monitors.py
│   │       └── jobs.py
│   │
│   ├── worker/
│   │   ├── celery_app.py
│   │   ├── schedules.py
│   │   └── tasks/
│   │       ├── collect.py
│   │       ├── parse.py
│   │       ├── translate.py
│   │       ├── extract.py
│   │       ├── resolve_entities.py
│   │       ├── verify.py
│   │       ├── calculate_risks.py
│   │       ├── update_scenarios.py
│   │       ├── generate_reports.py
│   │       └── dispatch_notifications.py
│   │
│   └── cli/
│       └── main.py
│
├── src/
│   └── mei/
│       ├── domain/
│       │   ├── actors/
│       │   ├── sources/
│       │   ├── documents/
│       │   ├── claims/
│       │   ├── events/
│       │   ├── evidence/
│       │   ├── relationships/
│       │   ├── indicators/
│       │   ├── risks/
│       │   ├── scenarios/
│       │   ├── investigations/
│       │   ├── reports/
│       │   └── forecasts/
│       │
│       ├── application/
│       │   ├── commands/
│       │   ├── queries/
│       │   ├── dto/
│       │   └── services/
│       │
│       ├── infrastructure/
│       │   ├── database/
│       │   ├── repositories/
│       │   ├── object_storage/
│       │   ├── collection/
│       │   ├── llm/
│       │   ├── translation/
│       │   ├── search/
│       │   ├── messaging/
│       │   └── auth/
│       │
│       └── shared/
│           ├── enums.py
│           ├── errors.py
│           ├── ids.py
│           ├── logging.py
│           ├── security.py
│           └── time.py
│
├── prompts/
│   ├── extraction/
│   ├── verification/
│   ├── relationships/
│   ├── risks/
│   ├── scenarios/
│   └── reports/
│
├── configs/
│   ├── actors.seed.yml
│   ├── countries.yml
│   ├── event-types.yml
│   ├── source-policy.yml
│   ├── risk-indicators.yml
│   ├── report-templates.yml
│   └── schedules.yml
│
├── migrations/
├── scripts/
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── contract/
│   ├── evaluation/
│   └── fixtures/
│
└── docs/
    ├── 01-project-idea.md
    ├── 02-implementation-design.md
    ├── api.md
    ├── data-model.md
    ├── source-policy.md
    ├── risk-methodology.md
    └── operations.md
```

---

## 6. Modular monolith boundaries

Each domain module contains:

- entities and value objects;
- domain rules;
- repository interfaces;
- commands and queries;
- application services;
- infrastructure adapters.

Cross-module writes should happen through application services or domain events, not through arbitrary imports of ORM models.

Initial modules:

1. identity and access;
2. actors;
3. sources and documents;
4. claims and evidence;
5. events;
6. relationships;
7. indicators and risks;
8. scenarios and forecasts;
9. investigations;
10. reports and notifications.

---

## 7. Persistence conventions

### 7.1 Identifiers

Use UUIDv7 identifiers for sortable, globally unique records.

### 7.2 Timestamps

- Store timestamps in UTC.
- Require timezone-aware values.
- Preserve source-local date text when parsing is uncertain.
- Use `valid_from` and `valid_to` for temporal facts.
- Use `recorded_at` for system observation time.

### 7.3 Soft deletion and supersession

Canonical intelligence records should rarely be hard-deleted. Use status, supersession links, and correction records.

### 7.4 JSONB

Use JSONB only for source-specific or extensible attributes. Important query dimensions must use typed columns and normalized tables.

---

## 8. Database model

The following is the initial logical schema. Exact indexes and constraints are refined during migration design.

### 8.1 Users and authorization

#### `users`

- `id`
- `email`
- `display_name`
- `status`
- `created_at`
- `updated_at`

#### `roles`

- `id`
- `name`

#### `user_roles`

- `user_id`
- `role_id`

#### `api_keys`

- `id`
- `user_id`
- `name`
- `key_hash`
- `scopes`
- `expires_at`
- `last_used_at`
- `revoked_at`

### 8.2 Actors

#### `actors`

- `id`
- `canonical_name`
- `native_name`
- `actor_type`
- `parent_actor_id`
- `country_actor_id`
- `status`
- `description`
- `valid_from`
- `valid_to`
- `attributes_json`
- `created_at`
- `updated_at`

#### `actor_aliases`

- `id`
- `actor_id`
- `alias`
- `language`
- `alias_type`
- `valid_from`
- `valid_to`

#### `actor_leadership`

- `id`
- `actor_id`
- `person_actor_id`
- `role_name`
- `valid_from`
- `valid_to`
- `evidence_bundle_id`

### 8.3 Sources and documents

#### `sources`

Represents a publisher, feed, account, database, or source system.

- `id`
- `name`
- `source_type`
- `base_url`
- `jurisdiction`
- `default_language`
- `ownership`
- `known_affiliations`
- `historical_reliability`
- `collection_policy`
- `enabled`
- `created_at`
- `updated_at`

#### `source_endpoints`

- `id`
- `source_id`
- `endpoint_type`
- `url`
- `schedule`
- `parser_name`
- `priority`
- `last_success_at`
- `last_failure_at`
- `failure_count`

#### `documents`

- `id`
- `source_id`
- `canonical_url`
- `external_id`
- `title`
- `original_language`
- `published_at`
- `retrieved_at`
- `content_hash`
- `raw_object_key`
- `normalized_object_key`
- `extracted_text`
- `translation_text`
- `parser_version`
- `status`
- `metadata_json`

#### `document_chunks`

- `id`
- `document_id`
- `sequence`
- `text`
- `token_count`
- `embedding`
- `metadata_json`

Use both PostgreSQL full-text indexes and pgvector indexes.

### 8.4 Claims and evidence

#### `claims`

- `id`
- `claim_text`
- `normalized_claim`
- `claim_type`
- `claimant_actor_id`
- `subject_actor_id`
- `event_id`
- `first_observed_at`
- `last_checked_at`
- `verification_status`
- `confidence`
- `lifecycle_status`
- `created_by_type`
- `created_by_id`
- `created_at`
- `updated_at`

#### `claim_evidence`

- `id`
- `claim_id`
- `document_id`
- `chunk_id`
- `stance`
- `excerpt`
- `source_location`
- `directness`
- `independence_group`
- `confidence`
- `analyst_note`
- `created_at`

#### `evidence_bundles`

- `id`
- `title`
- `summary`
- `confidence`
- `created_at`
- `approved_at`
- `approved_by`

#### `evidence_bundle_items`

- `bundle_id`
- `claim_evidence_id`
- `weight`

### 8.5 Events

#### `events`

- `id`
- `event_type`
- `title`
- `summary`
- `started_at`
- `ended_at`
- `time_precision`
- `severity`
- `strategic_significance`
- `verification_status`
- `confidence`
- `lifecycle_status`
- `evidence_bundle_id`
- `supersedes_event_id`
- `created_at`
- `updated_at`

#### `event_actors`

- `event_id`
- `actor_id`
- `role`
- `participation_status`
- `confidence`

#### `event_locations`

- `id`
- `event_id`
- `name`
- `country_actor_id`
- `latitude`
- `longitude`
- `location_precision`

#### `event_impacts`

- `id`
- `event_id`
- `impact_type`
- `magnitude`
- `unit`
- `estimate_low`
- `estimate_high`
- `confidence`
- `evidence_bundle_id`

### 8.6 Relationships

#### `relationships`

- `id`
- `source_actor_id`
- `target_actor_id`
- `relationship_type`
- `directionality`
- `valid_from`
- `valid_to`
- `status`

#### `relationship_observations`

- `id`
- `relationship_id`
- `observed_at`
- `diplomatic_score`
- `military_cooperation_score`
- `military_tension_score`
- `intelligence_cooperation_score`
- `economic_dependency_score`
- `energy_dependency_score`
- `strategic_trust_score`
- `ideological_compatibility_score`
- `proxy_competition_score`
- `public_hostility_score`
- `escalation_risk_score`
- `trend`
- `confidence`
- `explanation`
- `evidence_bundle_id`
- `ruleset_version`
- `model_version`
- `approved_at`
- `approved_by`

### 8.7 Indicators and risks

#### `indicator_definitions`

- `id`
- `code`
- `name`
- `description`
- `category`
- `value_type`
- `normalization_method`
- `default_weight`
- `active`
- `ruleset_version`

#### `indicator_observations`

- `id`
- `indicator_id`
- `scope_type`
- `scope_id`
- `observed_at`
- `raw_value`
- `normalized_value`
- `confidence`
- `evidence_bundle_id`
- `source_method`

#### `risk_definitions`

- `id`
- `code`
- `name`
- `description`
- `scope_types`
- `ruleset_version`

#### `risk_indicator_weights`

- `risk_definition_id`
- `indicator_definition_id`
- `weight`
- `direction`
- `conditions_json`

#### `risk_assessments`

- `id`
- `risk_definition_id`
- `scope_type`
- `scope_id`
- `assessed_at`
- `base_score`
- `llm_adjustment`
- `final_score`
- `previous_score`
- `trend`
- `confidence`
- `explanation`
- `counter_indicators`
- `evidence_bundle_id`
- `ruleset_version`
- `model_version`
- `approval_status`
- `approved_by`
- `approved_at`

### 8.8 Scenarios and forecasts

#### `scenarios`

- `id`
- `name`
- `scope_type`
- `scope_id`
- `scenario_family`
- `time_horizon`
- `status`
- `description`
- `created_at`
- `updated_at`

#### `scenario_assessments`

- `id`
- `scenario_id`
- `assessed_at`
- `probability_low`
- `probability_high`
- `confidence`
- `assumptions`
- `trigger_events`
- `leading_indicators`
- `expected_actor_behavior`
- `military_consequences`
- `economic_consequences`
- `humanitarian_consequences`
- `invalidation_criteria`
- `explanation_of_change`
- `evidence_bundle_id`
- `model_version`
- `approved_by`
- `approved_at`

#### `forecast_records`

- `id`
- `question`
- `issued_at`
- `resolution_date`
- `probability`
- `confidence`
- `assumptions`
- `evidence_bundle_id`
- `status`
- `outcome`
- `resolved_at`
- `brier_score`
- `evaluation_note`

### 8.9 Investigations

#### `investigations`

- `id`
- `title`
- `question`
- `status`
- `priority`
- `requested_by`
- `assigned_to`
- `created_at`
- `started_at`
- `completed_at`
- `result_summary`
- `confidence`
- `report_id`

#### `investigation_steps`

- `id`
- `investigation_id`
- `step_type`
- `sequence`
- `status`
- `input_json`
- `output_json`
- `started_at`
- `completed_at`
- `error_message`

### 8.10 Reports and monitors

#### `reports`

- `id`
- `report_type`
- `title`
- `scope_type`
- `scope_id`
- `period_start`
- `period_end`
- `content_markdown`
- `content_object_key`
- `status`
- `generated_by_model`
- `prompt_version`
- `approved_by`
- `approved_at`
- `published_at`

#### `monitors`

- `id`
- `name`
- `user_id`
- `monitor_type`
- `condition_json`
- `schedule`
- `delivery_channel`
- `enabled`
- `last_evaluated_at`
- `last_triggered_at`

#### `notifications`

- `id`
- `monitor_id`
- `report_id`
- `severity`
- `title`
- `body`
- `delivery_channel`
- `status`
- `sent_at`
- `error_message`

---

## 9. Domain enums

Initial enums should include:

```python
from enum import StrEnum


class ActorType(StrEnum):
    COUNTRY = "country"
    GOVERNMENT = "government"
    MINISTRY = "ministry"
    MILITARY = "military"
    INTELLIGENCE_SERVICE = "intelligence_service"
    POLITICAL_PARTY = "political_party"
    ARMED_GROUP = "armed_group"
    INTERNATIONAL_ORGANIZATION = "international_organization"
    COMPANY = "company"
    RELIGIOUS_INSTITUTION = "religious_institution"
    TRIBAL_ORGANIZATION = "tribal_organization"
    MEDIA_ORGANIZATION = "media_organization"
    INDIVIDUAL = "individual"
    INFORMAL_NETWORK = "informal_network"


class LifecycleStatus(StrEnum):
    OBSERVED = "observed"
    EXTRACTED = "extracted"
    ASSESSED = "assessed"
    APPROVED = "approved"
    SUPERSEDED = "superseded"
    REJECTED = "rejected"


class VerificationStatus(StrEnum):
    UNREVIEWED = "unreviewed"
    UNSUPPORTED = "unsupported"
    SINGLE_SOURCE = "single_source"
    PARTIALLY_CORROBORATED = "partially_corroborated"
    VERIFIED = "verified"
    DISPUTED = "disputed"
    CONTRADICTED = "contradicted"
    FALSE = "false"
    UNVERIFIABLE = "unverifiable"


class EvidenceStance(StrEnum):
    SUPPORTS = "supports"
    CONTRADICTS = "contradicts"
    PARTIALLY_SUPPORTS = "partially_supports"
    CONTEXTUALIZES = "contextualizes"
    REPEATS = "repeats"
```

---

## 10. Source collection pipeline

### 10.1 Pipeline stages

```text
Discover endpoint item
  → Fetch content
  → Validate URL and response
  → Archive raw bytes
  → Extract normalized text
  → Detect language
  → Translate when required
  → Calculate content hash
  → Detect exact and semantic duplicates
  → Classify relevance
  → Chunk and index content
  → Extract candidate actors, claims, events, dates, and locations
  → Resolve entities
  → Create evidence links
  → Queue verification
```

### 10.2 Idempotency

Every task must be safe to retry.

Recommended keys:

- source endpoint plus external item ID;
- normalized canonical URL;
- raw content hash;
- extraction operation ID;
- model and prompt version;
- job idempotency key.

### 10.3 HTTP security

The collector must:

- allow only HTTP and HTTPS;
- reject local, loopback, link-local, and private address ranges unless explicitly allowlisted;
- revalidate redirect targets;
- limit redirects;
- enforce response-size and timeout limits;
- validate MIME types;
- isolate browser workers;
- never pass page instructions to the agent control context.

### 10.4 Raw archive

Archive original bytes before transformation. Object keys should include date, source ID, document ID, and content hash.

Example:

```text
raw/2026/07/20/{source_id}/{document_id}-{sha256}.html
```

### 10.5 Parsing

Use a generic parser first, then source-specific adapters only when quality requires them. Store parser name and version on the document.

### 10.6 Translation

- Preserve original text.
- Store translation separately.
- Record translation model and version.
- Preserve uncertain named entities in original script.
- Avoid translating evidence excerpts when the original wording is analytically important.

---

## 11. Deduplication

Use a staged strategy:

1. exact external ID match;
2. canonical URL match;
3. raw content hash match;
4. normalized text fingerprint match;
5. semantic similarity within a publication-time window;
6. event-level clustering.

A duplicated article and a duplicated event are different concepts. Multiple independent articles may describe one event and must remain separate evidence items.

---

## 12. Entity resolution

### 12.1 Resolution inputs

- canonical names;
- aliases;
- native names;
- transliterations;
- actor type;
- parent organization;
- country;
- known leaders;
- geographic context;
- historical validity window.

### 12.2 Resolution process

1. exact normalized alias match;
2. source-specific alias rules;
3. fuzzy candidate generation;
4. contextual ranking;
5. confidence threshold;
6. manual review for ambiguous high-impact actors.

Never automatically merge actors when confidence is below the configured threshold.

### 12.3 Merge audit

Actor merges and splits must be reversible and audited.

---

## 13. LLM integration architecture

### 13.1 Provider abstraction

Create an internal interface:

```python
from typing import Protocol, TypeVar
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class StructuredLLM(Protocol):
    async def generate_structured(
        self,
        *,
        task_name: str,
        prompt_version: str,
        input_text: str,
        output_model: type[T],
        metadata: dict[str, str],
    ) -> T: ...
```

Adapters can support OpenAI-compatible APIs, local models, or other providers.

### 13.2 Structured outputs

All extraction and analytical operations must use validated Pydantic schemas. Invalid output should be rejected or retried with bounded attempts.

### 13.3 Prompt versioning

Store prompts in versioned files. Every model-generated record stores:

- provider;
- model;
- model configuration;
- prompt name;
- prompt version;
- input hash;
- output hash;
- timestamp;
- token and cost metadata where available.

### 13.4 Model responsibilities

Allowed:

- relevance classification;
- candidate entity extraction;
- candidate claim extraction;
- event extraction;
- contradiction discovery;
- evidence summarization;
- relationship-change recommendation;
- bounded risk adjustment;
- scenario drafting;
- report drafting.

Not allowed without deterministic validation or human approval:

- canonical attribution;
- autonomous approval of high-impact events;
- arbitrary risk scores;
- destructive writes;
- publication;
- unsupervised actor merges.

---

## 14. Claim extraction

### 14.1 Output schema

```python
class ExtractedClaim(BaseModel):
    text: str
    claimant_name: str | None
    subject_name: str | None
    claim_type: str
    event_reference: str | None
    source_excerpt: str
    temporal_reference: str | None
    location_reference: str | None
    extraction_confidence: float
```

### 14.2 Rules

- Keep each claim atomic.
- Preserve attribution.
- Do not convert reported speech to fact.
- Separate estimates from confirmed quantities.
- Record ambiguous temporal expressions.
- Keep casualty, damage, territorial, and attribution claims distinct.

---

## 15. Event extraction and clustering

### 15.1 Candidate event signature

Use:

- event type;
- time window;
- normalized location;
- primary actors;
- action type;
- target type.

### 15.2 Event clustering

New candidate events should be compared with existing events in a configurable time and geographic window. Similarity is advisory. High-impact merges require review.

### 15.3 Event promotion

Candidate event lifecycle:

```text
EXTRACTED → ASSESSED → APPROVED
```

The assessment service calculates corroboration, contradiction, source independence, and confidence.

---

## 16. Verification engine

### 16.1 Inputs

- claim evidence;
- source metadata;
- independence groups;
- directness;
- source correction history;
- contradictory evidence;
- imagery or structured data;
- capability consistency;
- analyst notes.

### 16.2 Source independence

Several articles that repeat one wire report count as one evidence lineage, not multiple independent confirmations.

### 16.3 Example result

```json
{
  "claim_id": "uuid",
  "status": "partially_corroborated",
  "confidence": 0.72,
  "supporting_evidence_ids": ["uuid"],
  "contradicting_evidence_ids": ["uuid"],
  "independent_support_count": 2,
  "unresolved_questions": [
    "The exact number of damaged structures remains uncertain."
  ],
  "recommended_action": "analyst_review"
}
```

### 16.4 Human-review triggers

Require review for:

- declaration of war;
- leader death or incapacitation;
- nuclear incident;
- attribution of major attacks;
- large casualty estimates;
- territorial control change;
- government collapse;
- ceasefire or treaty;
- chokepoint closure;
- direct entry of an external power.

---

## 17. Search and retrieval

Implement hybrid retrieval:

1. structured filters from PostgreSQL;
2. full-text search over documents and reports;
3. vector search over document chunks;
4. evidence-aware reranking;
5. permission filtering;
6. date and approval-status filtering.

System answers should prefer:

- approved structured records;
- assessed records clearly labeled as assessed;
- source documents only when the structured model is incomplete.

---

## 18. Risk engine

### 18.1 Deterministic base score

Each risk definition references weighted indicators.

Example interstate escalation model:

```text
20% direct military exchanges
15% force mobilization
15% attacks on strategic targets
10% escalation rhetoric
10% alliance activation
10% deterioration of diplomatic channels
10% civilian or infrastructure impact
10% geographic expansion
```

### 18.2 Normalization

Each indicator defines:

- source value;
- normalization method;
- confidence;
- staleness policy;
- upper and lower bounds.

### 18.3 Confidence adjustment

Low-confidence observations should reduce assessment confidence, not necessarily reduce the risk score itself.

### 18.4 LLM adjustment

The model may recommend a bounded adjustment, initially limited to `-10` through `+10`.

Required output:

```json
{
  "base_score": 67,
  "recommended_adjustment": 5,
  "rationale": [
    "The event crossed a previously observed target-category threshold."
  ],
  "counter_indicators": [
    "No broad force mobilization is currently observed."
  ],
  "confidence": 0.71
}
```

The deterministic engine validates the range and stores both the base and adjusted values.

### 18.5 Change explanation

Every score update must expose:

- previous score;
- current score;
- changed indicators;
- evidence;
- counter-indicators;
- LLM adjustment;
- ruleset version;
- confidence;
- approval state.

---

## 19. Scenario engine

### 19.1 Scenario families

- controlled de-escalation;
- managed confrontation;
- regional escalation;
- systemic regional war.

### 19.2 Update process

1. retrieve current approved events, risks, and relationships;
2. retrieve previous scenario assessment;
3. evaluate trigger and invalidation conditions;
4. produce a proposed probability range;
5. explain the change;
6. run consistency checks across scenario probabilities;
7. request approval where configured;
8. preserve previous assessment.

### 19.3 Simulation isolation

Hypothetical user simulations must run in a separate simulation context and must never update canonical production records.

---

## 20. Investigation workflow

### 20.1 State machine

```text
QUEUED
  → COLLECTING
  → EXTRACTING
  → RESOLVING
  → COMPARING_EVIDENCE
  → ASSESSING
  → AWAITING_REVIEW
  → COMPLETED
```

Failure states:

- retryable failure;
- blocked by missing source access;
- rejected as out of scope;
- canceled.

### 20.2 Investigation steps

A standard event investigation should:

1. parse the user question;
2. identify likely actors, dates, and locations;
3. search internal intelligence;
4. collect approved external sources if required;
5. extract claims;
6. identify evidence lineages;
7. compare support and contradiction;
8. retrieve historical context;
9. produce an assessment;
10. identify information gaps;
11. draft an investigation report;
12. request analyst review for high-impact conclusions.

### 20.3 Durability

Every step stores inputs, outputs, status, timestamps, and errors. A worker retry must resume from the last completed step.

---

## 21. FastAPI design

### 21.1 API conventions

- Base path: `/api/v1`
- JSON responses
- RFC 9457 problem details for errors
- cursor pagination
- idempotency keys for commands
- ETags for selected read resources
- request correlation IDs
- explicit `as_of` dates on time-sensitive queries

### 21.2 Read endpoints

```text
GET  /actors
GET  /actors/{actor_id}
GET  /actors/{actor_id}/timeline
GET  /events
GET  /events/{event_id}
GET  /claims/{claim_id}
GET  /claims/{claim_id}/evidence
GET  /relationships
GET  /relationships/{relationship_id}/history
GET  /risks
GET  /risks/{risk_id}/history
GET  /scenarios
GET  /investigations/{investigation_id}
GET  /reports
GET  /reports/{report_id}
GET  /jobs/{job_id}
```

### 21.3 Command endpoints

```text
POST /sources/submit
POST /investigations
POST /events/{event_id}/approve
POST /events/{event_id}/reject
POST /claims/{claim_id}/assess
POST /relationships/{relationship_id}/assess
POST /risks/recalculate
POST /scenarios/simulate
POST /reports/generate
POST /reports/{report_id}/approve
POST /monitors
PATCH /monitors/{monitor_id}
DELETE /monitors/{monitor_id}
```

### 21.4 Purpose-built intelligence query endpoints

Provide purpose-built endpoints rather than forcing callers to compose many low-level calls:

```text
POST /intelligence/search
POST /intelligence/country-brief
POST /intelligence/relationship-comparison
POST /intelligence/risk-explanation
POST /intelligence/event-investigation
POST /intelligence/daily-brief
POST /intelligence/scenario-simulation
```

---

## 22. Example API schema

```python
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class RiskDimension(BaseModel):
    score: int = Field(ge=0, le=100)
    previous_score: int | None = Field(default=None, ge=0, le=100)
    trend: str
    confidence: float = Field(ge=0, le=1)
    explanation: str
    changed_indicators: list[str]
    counter_indicators: list[str]
    evidence_ids: list[UUID]


class RelationshipComparisonRequest(BaseModel):
    relationship_ids: list[UUID] = Field(min_length=1, max_length=10)
    as_of: datetime
    include_evidence: bool = True


class RelationshipComparisonItem(BaseModel):
    relationship_id: UUID
    source_actor: str
    target_actor: str
    diplomatic: RiskDimension
    military_tension: RiskDimension
    economic_dependency: RiskDimension
    strategic_trust: RiskDimension
    proxy_competition: RiskDimension
    escalation_risk: RiskDimension
```

---

## 23. System integration & APIs

### 23.1 Boundary

The REST API is the primary application boundary. It provides authenticated access to intelligence capabilities, handling authorization, audit, and validation.

### 23.2 API Capabilities

The platform exposes endpoints organized into:
- **Read APIs**: Actor/country profiles, events, claims, relationships, risk scores, scenarios, reports, and job status.
- **Analytical APIs**: Event investigations, narrative comparisons, brief generation, and scenario simulations.
- **Controlled Write APIs**: Source submissions, analyst notes, event approval/rejection, report approvals, and monitor management.

---

## 24. Scheduling design

### 24.1 Python infrastructure schedules

Celery Beat maintains system jobs.

| Job | Initial frequency |
|---|---:|
| Collect critical feeds | Every 10 minutes |
| Collect normal feeds | Hourly |
| Retry failed endpoints | Every 30 minutes |
| Parse new documents | Event-driven |
| Translate required documents | Event-driven |
| Extract claims and events | Event-driven |
| Re-evaluate unresolved claims | Every 2 hours |
| Recalculate active conflict risks | Hourly |
| Refresh country indicators | Daily |
| Generate daily brief | Daily |
| Generate weekly outlook | Weekly |
| Evaluate monitors | Every 10 minutes |
| Audit source failures | Daily |
| Evaluate due forecasts | Daily |
| Archive or tier old raw data | Weekly |

### 24.2 User & Monitor schedules

User-defined monitor schedules represent automated tasks:

- send the daily brief;
- request a weekly report;
- monitor a named relationship;
- notify on threshold changes;
- remind an analyst about unresolved claims.

Scheduled jobs invoke API endpoints rather than reproducing the collection pipeline.

---

## 25. Report generation

### 25.1 Generation process

1. resolve report scope and period;
2. query approved records;
3. include assessed records only when the template allows and label them;
4. retrieve evidence summaries;
5. calculate material changes;
6. generate structured report sections;
7. validate all referenced IDs and dates;
8. render Markdown;
9. optionally render HTML or PDF;
10. request approval if publication is required;
11. store generated artifact and metadata.

### 25.2 Citation model

Reports should cite internal evidence identifiers and source links. A rendered report can expose human-friendly numbered citations while preserving internal IDs.

### 25.3 Daily brief sections

- executive assessment;
- material changes;
- active conflicts;
- country risk changes;
- relationship changes;
- diplomatic developments;
- energy and maritime developments;
- economic and sanctions developments;
- humanitarian conditions;
- disputed and unresolved claims;
- scenario changes;
- indicators to monitor.

---

## 26. Authentication and authorization

### 26.1 MVP authentication

Use local JWT authentication and API keys. A future enterprise version can integrate an external identity provider.

### 26.2 Scopes

Suggested scopes:

```text
intelligence:read
sources:submit
investigations:create
investigations:read
claims:assess
events:approve
relationships:assess
risks:recalculate
scenarios:simulate
reports:generate
reports:approve
monitors:manage
admin:configuration
```

### 26.3 Approval policy

Approval endpoints require:

- appropriate role and scope;
- explicit object version;
- optional confirmation token for agent-driven approval;
- audit reason;
- immutable audit entry.

---

## 27. Security design

### 27.1 Network boundaries

- API is the only application entry point to core intelligence services.
- PostgreSQL, Redis, and MinIO are private.
- Browser workers run separately with restricted network and filesystem access.
- Administrative endpoints can use a separate network or ingress policy.

### 27.2 Secrets

- Never store secrets in the repository.
- Use environment variables for local development.
- Use a secrets manager in production.
- Hash API keys and refresh tokens.
- Rotate connector credentials.

### 27.3 Prompt-injection controls

- Mark collected content as untrusted.
- Keep system instructions outside source content.
- Do not grant source-analysis models tool access.
- Validate all structured output.
- Require allowlisted tool calls.
- Prevent retrieved text from selecting tools or changing permissions.

### 27.4 File processing

- enforce file-size limits;
- validate content type independently of file extension;
- scan uploaded files;
- parse in a sandbox;
- reject active content where unnecessary;
- use signed object-storage URLs;
- prevent path traversal.

### 27.5 Audit log

Log:

- authentication events;
- API-key usage;
- tool calls;
- data mutations;
- approvals and rejections;
- prompt and model versions;
- report generation and publication;
- monitor changes;
- configuration changes.

---

## 28. Observability

### 28.1 Metrics

Track:

- source fetch success and latency;
- parser success rate;
- documents collected by source and language;
- duplicate rate;
- extraction failures;
- unresolved entity rate;
- claim verification status counts;
- investigation duration;
- Celery queue depth and task retries;
- risk-calculation duration;
- report generation success;
- API latency and errors;
- LLM tokens, cost, validation failures, and retries.

### 28.2 Tracing

Use one trace across:

- API request;
- investigation creation;
- Celery workflow;
- LLM calls;
- database writes;
- report generation.

### 28.3 Health endpoints

```text
GET /health/live
GET /health/ready
GET /health/dependencies
```

Readiness should verify PostgreSQL and required configuration. Dependency health can report Redis, object storage, and provider status without exposing secrets.

---

## 29. Testing strategy

### 29.1 Unit tests

Test:

- domain state transitions;
- risk formulas;
- score bounds;
- confidence calculations;
- scenario probability validation;
- alias normalization;
- URL security rules;
- authorization policies.

### 29.2 Integration tests

Use testcontainers for:

- PostgreSQL and pgvector;
- Redis;
- MinIO;
- migration verification;
- repository behavior;
- Celery task idempotency.

### 29.3 Contract tests

- FastAPI schemas;
- source adapter interfaces;
- LLM structured outputs.

### 29.4 Evaluation tests

Maintain curated multilingual fixtures for:

- event extraction;
- claim attribution;
- actor resolution;
- duplicate detection;
- contradiction detection;
- report factual consistency;
- prompt-injection resistance.

### 29.5 Golden reports

Store approved small report fixtures and compare section structure, cited evidence, dates, and unsupported-claim rate.

### 29.6 Security tests

- SSRF attempts;
- redirect-to-private-network attempts;
- oversized documents;
- malicious HTML and document content;
- prompt injection;
- unauthorized tool calls;
- privilege escalation;
- replayed approval commands.

---

## 30. Local development deployment

### 30.1 Docker Compose services

```text
api
worker
beat
postgres
redis
minio
prometheus
grafana
```

### 30.2 Environment variables

```text
APP_ENV
APP_SECRET_KEY
DATABASE_URL
REDIS_URL
S3_ENDPOINT_URL
S3_ACCESS_KEY
S3_SECRET_KEY
S3_BUCKET
LLM_PROVIDER
LLM_MODEL
LLM_API_KEY
JWT_ISSUER
JWT_AUDIENCE
```

### 30.3 Development commands

The Makefile should eventually include:

```text
make install
make dev
make worker
make migrate
make seed
make test
make lint
make typecheck
make compose-up
make compose-down
```

---

## 31. Production deployment

### 31.1 Initial production target

Deploy to a single secured Linux server using Docker Compose or Dokploy.

Suggested separation:

- public or VPN-protected API ingress;
- private database network;
- separate browser-worker container;
- persistent PostgreSQL and MinIO volumes;
- off-server backups;
- TLS termination through Traefik or Nginx.

### 31.2 Backups

- daily PostgreSQL backup;
- object-storage replication or backup;
- encrypted off-server retention;
- periodic restore test;
- configuration and prompt-version backup.

### 31.3 Scaling path

Scale workers by queue:

- collection;
- browser;
- extraction;
- analysis;
- reporting.

Split services only after measured load or organizational requirements justify it.

---

## 32. CI/CD

Initial GitHub Actions workflows:

### Pull request checks

- Ruff check;
- Ruff format check;
- mypy;
- pytest unit tests;
- integration tests;
- Alembic migration check;
- dependency vulnerability scan;
- secret scan.

### Main branch

- build Docker image;
- run full test suite;
- publish versioned image;
- optionally deploy to staging;
- run health and migration checks.

Do not auto-deploy database migrations to production without a controlled release step.

---

## 33. Seed data

The initial seed should include:

- core countries;
- external powers;
- major international organizations;
- major regional armed and political organizations;
- actor aliases in relevant languages;
- event types;
- relationship dimensions;
- risk definitions;
- approximately 20 initial indicators;
- report templates;
- source registry entries.

Seed data must be versioned and idempotent.

---

## 34. Initial risk indicators

Suggested MVP indicators:

1. direct cross-border attacks;
2. missile and drone launch frequency;
3. force mobilization;
4. strategic-target attacks;
5. attacks on civilian infrastructure;
6. official escalation rhetoric;
7. evacuation or airspace closure;
8. alliance military activation;
9. diplomatic-contact deterioration;
10. ceasefire violations;
11. proxy-group mobilization;
12. maritime attack frequency;
13. shipping diversion;
14. insurance or freight-rate shock;
15. oil and gas export disruption;
16. sanctions expansion;
17. internal protest intensity;
18. elite defection or leadership instability;
19. humanitarian access deterioration;
20. nuclear inspection or enrichment deterioration.

Each indicator needs a precise definition, input source, update frequency, normalization function, confidence policy, and staleness rule.

---

## 35. Implementation phases

### Phase 0 — Repository and standards

Deliver:

- project documentation;
- Python package skeleton;
- lint, type-check, and test configuration;
- Docker Compose foundation;
- contribution and architecture rules.

### Phase 1 — Intelligence foundation

Deliver:

- FastAPI application;
- PostgreSQL models and Alembic;
- actor, source, document, claim, evidence, and event modules;
- authentication and scoped API keys;
- manual source submission;
- raw object storage;
- basic read APIs;
- audit logging.

Acceptance criteria:

- a user can submit a URL or document;
- raw content is archived;
- extracted text is stored;
- an analyst can create and approve an event with linked evidence.

### Phase 2 — Automated collection and extraction

Deliver:

- RSS and HTTP collectors;
- source registry and schedules;
- parsing, language detection, and translation;
- deduplication;
- LLM claim and event extraction;
- entity resolution;
- review queues.

Acceptance criteria:

- curated sources are collected automatically;
- duplicate content is recognized;
- candidate events and claims are created with provenance;
- ambiguous actor resolution is sent for review.

### Phase 3 — Relationships and risk engine

Deliver:

- relationship model and observations;
- indicator definitions and observations;
- deterministic risk calculation;
- bounded LLM adjustment;
- risk history and explanation APIs;
- country and relationship briefs.

Acceptance criteria:

- a risk score can be reproduced from stored indicators;
- every change exposes evidence and contributions;
- relationship history is queryable by date.

### Phase 4 — Scenarios, reports, and forecast audit

Deliver:

- scenario register;
- scenario update workflow;
- daily and weekly reports;
- forecast records and outcome evaluation;
- report approval and artifact storage.

Acceptance criteria:

- scenario changes preserve prior versions;
- reports cite internal evidence;
- forecasts can be scored after resolution.

### Phase 5 — Investigations & Monitors

Deliver:

- HTTPS tool / API endpoints;
- read and analytical tools;
- investigation launch and job status;
- report generation;
- monitor management;
- one delivery channel, preferably Telegram.

Acceptance criteria:

- APIs retrieve current data before answering;
- read and write permissions are separate;
- approval tools require explicit confirmation;
- user-facing jobs are durable and observable.

### Phase 6 — Advanced analysis

Possible deliverables:

- graph analytics;
- geospatial UI;
- commercial maritime data;
- imagery evidence;
- multi-model review;
- analyst disagreement;
- calibration dashboards;
- enterprise identity and tenancy.

---

## 36. MVP delivery backlog

### Epic A — Foundation

- initialize Python project;
- add settings and dependency injection;
- add structured logging;
- add Docker Compose;
- add PostgreSQL, Redis, and MinIO;
- add CI.

### Epic B — Actors

- actor CRUD;
- aliases;
- temporal validity;
- seed data;
- entity search.

### Epic C — Sources and documents

- source registry;
- manual URL submission;
- fetch security;
- raw archive;
- parser;
- chunks and search.

### Epic D — Claims, evidence, and events

- structured extraction;
- claim storage;
- evidence links;
- event clustering;
- assessment and approval.

### Epic E — Relationships and risk

- relationship observations;
- indicator definitions;
- risk formulas;
- history and explanation.

### Epic F — Investigations and reports

- investigation state machine;
- Celery orchestration;
- daily brief;
- investigation report;
- approval and artifact storage.

### Epic G — Operational APIs & Monitors

- API endpoints;
- system tools;
- scoped credentials;
- monitor and alert flow.

---

## 37. Definition of done

A feature is complete when:

- domain rules are implemented;
- API or task interface is documented;
- authorization is enforced;
- audit records are written;
- unit and integration tests pass;
- failure and retry behavior is defined;
- observability is present;
- migrations are reversible where practical;
- source and evidence provenance is preserved;
- no unverified fact is silently promoted;
- documentation is updated.

---

## 38. Key architectural decisions

### ADR-001: Modular monolith first

Reason: simpler deployment and transactions, while preserving domain boundaries.

### ADR-002: PostgreSQL before graph database

Reason: relational integrity and temporal records are primary. NetworkX supports initial graph analysis. Add Neo4j only when real graph-query requirements justify it.

### ADR-003: Celery before Temporal

Reason: the MVP jobs are straightforward enough for Celery. Investigation steps are persisted to support recovery. Reassess when workflows become significantly more complex.

### ADR-004: API is the security boundary

Reason: prevents external callers from becoming privileged database clients and keeps authorization, audit, and validation centralized.

### ADR-005: Human approval for high-impact intelligence

Reason: attribution, casualty, leadership, nuclear, territorial, and war-status claims are too consequential for autonomous promotion.

### ADR-006: Deterministic risk base with bounded LLM adjustment

Reason: combines reproducibility with contextual interpretation while limiting opaque model influence.

### ADR-007: Curated sources before open-web autonomy

Reason: improves reliability, legal clarity, parser quality, and operational control.

---

## 39. First implementation milestone

The first coding milestone should produce a runnable vertical slice:

1. Docker Compose starts PostgreSQL, Redis, MinIO, API, worker, and Beat.
2. Alembic creates users, actors, sources, documents, claims, evidence, and events.
3. A user authenticates with an API key.
4. The user submits a source URL.
5. A background task safely fetches and archives it.
6. The parser extracts text.
7. A structured model extracts candidate claims and an event.
8. An analyst reviews and approves the event.
9. The API returns the event with supporting and contradictory evidence.
10. System API clients can query the approved event through read-only endpoints.

This validates the central architecture before relationship scoring, scenarios, broad automation, or advanced reporting are added.

---

## 40. Final implementation recommendation

Use the following operational division:

```text
FastAPI
  Authenticated and audited access to intelligence capabilities

Application and domain services
  Intelligence rules, lifecycle, approvals, and orchestration

Celery and Redis
  Durable collection, extraction, verification, scoring, and reporting jobs

PostgreSQL and pgvector
  Authoritative structured intelligence, history, lexical search, and vectors

MinIO or S3
  Original sources, normalized documents, and generated artifacts

LLMs
  Structured extraction, evidence comparison, bounded interpretation, and drafting

Rules and analysts
  Verification, explainability, approval, correction, and accountability
```

The next repository change after these documents should be Phase 0: initialize the Python package, Docker Compose stack, development tooling, and first architecture skeleton.