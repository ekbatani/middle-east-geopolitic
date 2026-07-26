# Middle East Geopolitical Intelligence Platform — Data Model Guide

This document describes the persistence models, database schema conventions, relationships, and indexing strategies used in PostgreSQL and MinIO.

---

## 1. Schema Principles

1. **UUIDv7 Primary Keys**: All primary identifiers use sortable UUIDv7 strings for global uniqueness and temporal ordering.
2. **Strict Time Awareness**: Records use `valid_from` / `valid_to` for temporal domain facts and `recorded_at` for system observation timestamps.
3. **Auditable Evidence Provenance**: Claims and facts link directly to source documents and chunk IDs via `claim_evidence` and `evidence_bundles`.
4. **Hybrid Search**: Standard relational columns for query dimensions, PostgreSQL full-text search (`tsvector`) for lexical search, and `pgvector` (`vector(1536)`) for semantic embeddings.

---

## 2. Core Entities & Tables

### 2.1 Actors & Aliases
- `actors`: Core table storing canonical name, native name, actor type (`country`, `government`, `military`, `armed_group`, etc.), parent actor ID, and validity range.
- `actor_aliases`: Stores alternative spellings, native script variants, acronyms, and former names.
- `actor_leadership`: Tracks key leadership positions over time.

### 2.2 Sources, Documents & Chunks
- `sources`: Source registry tracking publisher, jurisdiction, default language, reliability rating, and collection policies.
- `documents`: Raw and parsed articles/reports, canonical URL, SHA-256 hash, raw MinIO object key, extracted text, and translation.
- `document_chunks`: Text chunks with token counts, vector embeddings (`vector`), and search indexes.

### 2.3 Claims & Evidence
- `claims`: Atomic assertions made by actors or sources, storing claimant, subject, claim type, and verification status.
- `claim_evidence`: Links chunks to claims with stance (`supports`, `contradicts`, `partially_supports`, `contextualizes`, `repeats`) and directness attributes.
- `evidence_bundles`: Grouping of evidence supporting approved canonical events.

### 2.4 Events & Impacts
- `events`: Time-bounded occurrences with event type, severity, strategic significance, and verification status (`unreviewed`, `verified`, `disputed`, `false`).
- `event_actors`: Many-to-many link between events and actors with participant roles.
- `event_locations`: Spatial location data (latitude, longitude, country).
- `event_impacts`: Casualty, damage, and economic impact estimates with upper/lower bounds and confidence scores.

### 2.5 Relationships & Observations
- `relationships`: Durable bilateral connections between source and target actors.
- `relationship_observations`: Time-stamped multidimensional scores (diplomatic, military tension, strategic trust, proxy competition, economic dependency).

### 2.6 Indicators & Risk Assessments
- `indicator_definitions`: Defined indicators (e.g. `direct_cross_border_attacks`, `force_mobilization`, `maritime_attack_frequency`).
- `indicator_observations`: Measured or observed normalized values (`0.0` to `1.0`) with confidence metadata.
- `risk_assessments`: Calculated risk scores storing base score, bounded LLM adjustment (`-10` to `+10`), final score (`0`-`100`), trend, and counter-indicators.

### 2.7 Scenarios & Forecasts
- `scenarios`: Scenario definitions across four families (`controlled_deescalation`, `managed_confrontation`, `regional_escalation`, `systemic_regional_war`).
- `scenario_assessments`: Evaluated probability ranges, triggers, leading indicators, and invalidation criteria.
- `forecast_records`: Bounded probabilistic predictions scored post-resolution using Brier scores.

---

## 3. Storage Layout (MinIO / S3)

- `raw/{YYYY}/{MM}/{DD}/{source_id}/{document_id}.html`: Original untouched raw HTML/JSON bytes.
- `normalized/{YYYY}/{MM}/{DD}/{document_id}.json`: Parsed and extracted document structure.
- `reports/{YYYY}/{MM}/{report_id}.md`: Generated markdown and rendered report artifacts.
- `imagery/{YYYY}/{MM}/{image_id}.png`: Source imagery evidence artifacts.
