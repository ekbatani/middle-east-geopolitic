# Middle East Geopolitical Intelligence Platform — Data Model Guide

This document describes the persistence models, database schema conventions, relationships, and indexing strategies used in PostgreSQL (with `pgvector`) and MinIO / S3 Object Storage.

---

## 1. Schema Principles

1. **UUIDv7 Primary Keys**: All primary identifiers use sortable UUIDv7 strings for global uniqueness and temporal ordering.
2. **Strict Time Awareness**: Records use `valid_from` / `valid_to` for temporal domain facts and `recorded_at` for system observation timestamps.
3. **Auditable Evidence Provenance**: Claims and facts link directly to source documents and chunk IDs via `claim_evidence` and `evidence_bundles`.
4. **Hybrid Search**: Standard relational columns for query dimensions, PostgreSQL full-text search (`tsvector`) for lexical search, and `pgvector` (`vector(1536)`) for semantic embeddings.

---

## 2. Core Entities & Schema Overview

### 2.1 Actors & Aliases (Phase 1)
- `actors`: Canonical actor profiles storing name, native name, actor type (`country`, `government`, `military`, `armed_group`, `international_org`, etc.), parent actor ID, and temporal validity.
- `actor_aliases`: Alternative spellings, native script variants, acronyms, and former names.
- `actor_leadership`: Key leadership positions and biographical links tracked over time.

### 2.2 Sources, Documents & Chunks (Phase 1 & 2)
- `sources`: Source registry tracking publisher, jurisdiction, default language, reliability rating, and collection frequency.
- `documents`: Raw and parsed articles/reports, canonical URL, SHA-256 hash, raw MinIO object key, extracted text, and translation.
- `document_chunks`: Text chunks with token counts, vector embeddings (`vector(1536)`), and tsvector search indexes.

### 2.3 Claims & Verification Evidence (Phase 1 & 2)
- `claims`: Atomic assertions made by actors or sources, storing claimant, subject, claim type, and verification status (`unverified`, `supported`, `disputed`, `debunked`).
- `claim_evidence`: Links document chunks to claims with stance (`supports`, `contradicts`, `partially_supports`, `contextualizes`, `repeats`) and directness attributes.
- `evidence_bundles`: Grouping of verified evidence supporting canonical events.

### 2.4 Events & Impacts (Phase 1 & 2)
- `events`: Time-bounded kinetic, diplomatic, or political occurrences with event type, severity, strategic significance, and verification status (`unreviewed`, `verified`, `disputed`, `false`).
- `event_actors`: Many-to-many link between events and actors with participant roles (`initiator`, `target`, `mediator`, `affected`).
- `event_locations`: Spatial location data (latitude, longitude, region, country).
- `event_impacts`: Casualty, infrastructure damage, and economic impact estimates with upper/lower bounds and confidence scores.

### 2.5 Relationships & Observations (Phase 3)
- `relationships`: Durable bilateral connections between source and target actors.
- `relationship_observations`: Time-stamped multidimensional scores (diplomatic status, military tension, strategic trust, proxy competition, economic dependency).

### 2.6 Indicators & Risk Assessments (Phase 3)
- `indicator_definitions`: Defined indicators (e.g. `IND_DIRECT_ATTACKS`, `IND_FORCE_MOBILIZATION`, `IND_MARITIME_DISRUPTION`).
- `indicator_observations`: Measured or observed normalized values (`0.0` to `1.0`) with confidence metadata.
- `risk_assessments`: Calculated risk scores storing base score, bounded LLM adjustment (`-10` to `+10`), final score (`0`-`100`), trend, and counter-indicators.

### 2.7 Scenarios & Forecasts (Phase 4)
- `scenarios`: Scenario definitions across four families (`controlled_deescalation`, `managed_confrontation`, `regional_escalation`, `systemic_regional_war`).
- `scenario_assessments`: Evaluated probability ranges, triggers, leading indicators, and invalidation criteria.
- `forecast_records`: Bounded probabilistic predictions scored post-resolution using Brier scores.

### 2.8 Investigations & Monitors (Phase 5)
- `investigations`: Intelligence investigation records tracking target subjects, scope, assigned analyst, and state.
- `investigation_notes`: Analytical findings, evidence references, and progress logs.
- `monitors`: Automated monitoring rules tracking indicator thresholds or keyword triggers.
- `monitor_alerts`: Generated alert notifications when monitor conditions are breached.

### 2.9 Advanced Analytics & Evidence (Phase 6)
- `graph_nodes` & `graph_edges`: Topology node and edge entities representing multi-relational intelligence networks.
- `calibration_records`: Audit history comparing predicted scenario probabilities against historical outcomes.
- `analyst_disagreements`: Tracking stance divergence among analysts on disputed events or risk scores.
- `multi_model_reviews`: Records of cross-model LLM comparisons evaluating candidate claims.
- `imagery_evidence`: Metadata for satellite or open-source image evidence, including bounding boxes, geographic coordinates, and verification tags.

---

## 3. Storage Layout (MinIO / S3)

- `raw/{YYYY}/{MM}/{DD}/{source_id}/{document_id}.html`: Original untouched raw HTML/JSON bytes.
- `normalized/{YYYY}/{MM}/{DD}/{document_id}.json`: Parsed and extracted document structure.
- `reports/{YYYY}/{MM}/{report_id}.md`: Generated markdown and rendered report artifacts.
- `imagery/{YYYY}/{MM}/{image_id}.png`: Source imagery evidence artifacts.
