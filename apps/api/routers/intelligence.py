"""Purpose-built, read-only intelligence endpoints for Hermes (design doc section 21.4)."""

from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy import select

from apps.api.dependencies import SessionDep, require_scopes
from apps.api.routers.reports import ReportOut
from apps.api.routers.scenarios import ScenarioSimulationRequest
from mei.application.services.investigations import InvestigationService
from mei.application.services.report_generator import ReportGenerator
from mei.application.services.risk_engine import diff_changed_indicators
from mei.application.services.scenario_engine import ScenarioEngine, ScenarioUpdateRecommendation
from mei.domain.actors.models import Actor
from mei.domain.claims.models import Claim
from mei.domain.documents.models import Document
from mei.domain.events.models import Event
from mei.infrastructure.auth.principal import Principal
from mei.infrastructure.llm.factory import get_structured_llm
from mei.infrastructure.llm.protocol import StructuredLLM
from mei.infrastructure.repositories.actors import ActorRepository
from mei.infrastructure.repositories.events import EventRepository
from mei.infrastructure.repositories.evidence import EvidenceRepository
from mei.infrastructure.repositories.relationships import RelationshipRepository
from mei.infrastructure.repositories.risks import RiskRepository
from mei.shared.enums import ActorType, Scope, ScopeType, Trend
from mei.shared.errors import LLMConfigurationError, NotFoundError, ValidationError
from mei.shared.time import utcnow

router = APIRouter(prefix="/intelligence", tags=["intelligence"])


ReadPrincipal = Annotated[Principal, Depends(require_scopes(Scope.INTELLIGENCE_READ))]

_DIMENSION_EPSILON = 2  # score points; matches RiskEngine's trend threshold.


class RiskDimension(BaseModel):
    """Design doc section 22, verbatim."""

    score: int = Field(ge=0, le=100)
    previous_score: int | None = Field(default=None, ge=0, le=100)
    trend: str
    confidence: float = Field(ge=0, le=1)
    explanation: str
    changed_indicators: list[str]
    counter_indicators: list[str]
    evidence_ids: list[UUID]


def _score_trend(score: int, previous_score: int | None) -> str:
    if previous_score is None:
        return str(Trend.STABLE)
    delta = score - previous_score
    if delta > _DIMENSION_EPSILON:
        return str(Trend.RISING)
    if delta < -_DIMENSION_EPSILON:
        return str(Trend.FALLING)
    return str(Trend.STABLE)


# --- relationship-comparison -------------------------------------------------


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


_COMPARISON_FIELDS: dict[str, str] = {
    "diplomatic": "diplomatic_score",
    "military_tension": "military_tension_score",
    "economic_dependency": "economic_dependency_score",
    "strategic_trust": "strategic_trust_score",
    "proxy_competition": "proxy_competition_score",
    "escalation_risk": "escalation_risk_score",
}


@router.post("/relationship-comparison", response_model=list[RelationshipComparisonItem])
async def relationship_comparison(
    payload: RelationshipComparisonRequest, session: SessionDep, _principal: ReadPrincipal
) -> list[RelationshipComparisonItem]:
    relationships_repo = RelationshipRepository(session)
    actors_repo = ActorRepository(session)
    evidence_repo = EvidenceRepository(session)

    items: list[RelationshipComparisonItem] = []
    for relationship_id in payload.relationship_ids:
        relationship = await relationships_repo.get(relationship_id)
        if relationship is None:
            raise NotFoundError(f"Relationship {relationship_id} not found")

        current = await relationships_repo.get_latest_observation(
            relationship_id, as_of=payload.as_of
        )
        if current is None:
            raise NotFoundError(
                f"Relationship {relationship_id} has no observation as of {payload.as_of}"
            )
        previous = await relationships_repo.get_previous_observation(
            relationship_id, before=current.observed_at
        )

        source_actor = await actors_repo.get(relationship.source_actor_id)
        target_actor = await actors_repo.get(relationship.target_actor_id)

        evidence_ids: list[UUID] = []
        if payload.include_evidence and current.evidence_bundle_id is not None:
            evidence_ids = await evidence_repo.list_item_claim_evidence_ids(
                current.evidence_bundle_id
            )

        dimensions: dict[str, RiskDimension] = {}
        for name, field in _COMPARISON_FIELDS.items():
            score = getattr(current, field) or 0
            previous_score = getattr(previous, field) if previous else None
            dimensions[name] = RiskDimension(
                score=score,
                previous_score=previous_score,
                trend=_score_trend(score, previous_score),
                confidence=current.confidence or 0.0,
                explanation=current.explanation or "",
                # Relationship dimensions are analyst-scored as a whole
                # rather than built from weighted sub-indicators, so there
                # is no lower-level breakdown to diff or counter here.
                changed_indicators=[],
                counter_indicators=[],
                evidence_ids=evidence_ids,
            )

        items.append(
            RelationshipComparisonItem(
                relationship_id=relationship_id,
                source_actor=source_actor.canonical_name if source_actor else "unknown",
                target_actor=target_actor.canonical_name if target_actor else "unknown",
                **dimensions,
            )
        )

    return items


# --- risk-explanation ---------------------------------------------------------


class RiskExplanationRequest(BaseModel):
    risk_definition_id: UUID
    scope_type: ScopeType
    scope_id: UUID | None = None
    as_of: datetime | None = None


class ContributionOut(BaseModel):
    indicator_code: str
    indicator_name: str
    weight: float
    direction: str
    raw_value: float | None
    normalized_value: float | None
    contribution: float | None
    confidence: float | None
    observed_at: str | None
    included: bool
    stale: bool


class RiskExplanationResponse(BaseModel):
    risk_definition_id: UUID
    risk_code: str
    risk_name: str
    scope_type: ScopeType
    scope_id: UUID | None
    assessed_at: datetime
    base_score: int
    llm_adjustment: int
    final_score: int
    previous_score: int | None
    trend: str
    confidence: float
    explanation: str
    changed_indicators: list[str]
    counter_indicators: list[str]
    contributions: list[ContributionOut]
    evidence_ids: list[UUID]
    ruleset_version: str
    model_version: str | None


@router.post("/risk-explanation", response_model=RiskExplanationResponse)
async def risk_explanation(
    payload: RiskExplanationRequest, session: SessionDep, _principal: ReadPrincipal
) -> RiskExplanationResponse:
    risks_repo = RiskRepository(session)
    evidence_repo = EvidenceRepository(session)

    definition = await risks_repo.get_definition(payload.risk_definition_id)
    if definition is None:
        raise NotFoundError(f"Risk definition {payload.risk_definition_id} not found")

    assessment = await risks_repo.get_latest_assessment(
        risk_definition_id=payload.risk_definition_id,
        scope_type=payload.scope_type,
        scope_id=payload.scope_id,
        as_of=payload.as_of,
    )
    if assessment is None:
        raise NotFoundError(
            f"No risk assessment found for '{definition.code}' at the requested scope"
        )

    previous = await risks_repo.get_previous_assessment(
        risk_definition_id=payload.risk_definition_id,
        scope_type=payload.scope_type,
        scope_id=payload.scope_id,
        before=assessment.assessed_at,
    )

    changed_indicators = diff_changed_indicators(
        previous.contributions_json if previous else None, assessment.contributions_json
    )

    evidence_ids: list[UUID] = []
    if assessment.evidence_bundle_id is not None:
        evidence_ids = await evidence_repo.list_item_claim_evidence_ids(
            assessment.evidence_bundle_id
        )

    return RiskExplanationResponse(
        risk_definition_id=definition.id,
        risk_code=definition.code,
        risk_name=definition.name,
        scope_type=assessment.scope_type,
        scope_id=assessment.scope_id,
        assessed_at=assessment.assessed_at,
        base_score=assessment.base_score,
        llm_adjustment=assessment.llm_adjustment,
        final_score=assessment.final_score,
        previous_score=assessment.previous_score,
        trend=str(assessment.trend) if assessment.trend else str(Trend.STABLE),
        confidence=assessment.confidence,
        explanation=assessment.explanation or "",
        changed_indicators=changed_indicators,
        counter_indicators=list(assessment.counter_indicators_json),
        contributions=[ContributionOut.model_validate(c) for c in assessment.contributions_json],
        evidence_ids=evidence_ids,
        ruleset_version=assessment.ruleset_version,
        model_version=assessment.model_version,
    )


# --- country-brief --------------------------------------------------------


class CountryBriefRequest(BaseModel):
    country_actor_id: UUID
    as_of: datetime | None = None


class CountryBriefRiskOut(BaseModel):
    risk_code: str
    risk_name: str
    dimension: RiskDimension


class CountryBriefRelationshipOut(BaseModel):
    relationship_id: UUID
    counterpart_actor_id: UUID
    counterpart_name: str
    relationship_type: str
    escalation_risk_score: int | None
    trend: str | None
    confidence: float | None


class CountryBriefResponse(BaseModel):
    country_actor_id: UUID
    country_name: str
    as_of: datetime
    risks: list[CountryBriefRiskOut]
    relationships: list[CountryBriefRelationshipOut]


@router.post("/country-brief", response_model=CountryBriefResponse)
async def country_brief(
    payload: CountryBriefRequest, session: SessionDep, _principal: ReadPrincipal
) -> CountryBriefResponse:
    actors_repo = ActorRepository(session)
    risks_repo = RiskRepository(session)
    relationships_repo = RelationshipRepository(session)
    evidence_repo = EvidenceRepository(session)

    country = await actors_repo.get(payload.country_actor_id)
    if country is None:
        raise NotFoundError(f"Actor {payload.country_actor_id} not found")
    if country.actor_type != ActorType.COUNTRY:
        raise ValidationError(f"Actor {payload.country_actor_id} is not a country")

    as_of = payload.as_of or utcnow()

    risk_items: list[CountryBriefRiskOut] = []
    for definition in await risks_repo.list_definitions():
        if ScopeType.COUNTRY.value not in definition.scope_types:
            continue
        assessment = await risks_repo.get_latest_assessment(
            risk_definition_id=definition.id,
            scope_type=ScopeType.COUNTRY,
            scope_id=country.id,
            as_of=as_of,
        )
        if assessment is None:
            continue
        previous = await risks_repo.get_previous_assessment(
            risk_definition_id=definition.id,
            scope_type=ScopeType.COUNTRY,
            scope_id=country.id,
            before=assessment.assessed_at,
        )
        evidence_ids: list[UUID] = []
        if assessment.evidence_bundle_id is not None:
            evidence_ids = await evidence_repo.list_item_claim_evidence_ids(
                assessment.evidence_bundle_id
            )
        risk_items.append(
            CountryBriefRiskOut(
                risk_code=definition.code,
                risk_name=definition.name,
                dimension=RiskDimension(
                    score=assessment.final_score,
                    previous_score=assessment.previous_score,
                    trend=str(assessment.trend) if assessment.trend else str(Trend.STABLE),
                    confidence=assessment.confidence,
                    explanation=assessment.explanation or "",
                    changed_indicators=diff_changed_indicators(
                        previous.contributions_json if previous else None,
                        assessment.contributions_json,
                    ),
                    counter_indicators=list(assessment.counter_indicators_json),
                    evidence_ids=evidence_ids,
                ),
            )
        )

    relationship_items: list[CountryBriefRelationshipOut] = []
    for relationship in await relationships_repo.list_all(actor_id=country.id, limit=200):
        counterpart_id = (
            relationship.target_actor_id
            if relationship.source_actor_id == country.id
            else relationship.source_actor_id
        )
        counterpart = await actors_repo.get(counterpart_id)
        observation = await relationships_repo.get_latest_observation(relationship.id, as_of=as_of)
        relationship_items.append(
            CountryBriefRelationshipOut(
                relationship_id=relationship.id,
                counterpart_actor_id=counterpart_id,
                counterpart_name=counterpart.canonical_name if counterpart else "unknown",
                relationship_type=relationship.relationship_type,
                escalation_risk_score=observation.escalation_risk_score if observation else None,
                trend=str(observation.trend) if observation and observation.trend else None,
                confidence=observation.confidence if observation else None,
            )
        )

    return CountryBriefResponse(
        country_actor_id=country.id,
        country_name=country.canonical_name,
        as_of=as_of,
        risks=risk_items,
        relationships=relationship_items,
    )


# --- search, event-investigation, daily-brief, scenario-simulation -------------


def _try_get_llm() -> StructuredLLM | None:
    try:
        return get_structured_llm()
    except LLMConfigurationError:
        return None


class SearchItem(BaseModel):
    id: UUID
    type: str  # actor, event, claim, document
    title: str
    detail: str | None = None


class IntelligenceSearchRequest(BaseModel):
    query: str
    limit: int = 50


@router.post("/search", response_model=list[SearchItem])
async def search_intelligence(
    payload: IntelligenceSearchRequest,
    session: SessionDep,
    _principal: ReadPrincipal,
) -> list[SearchItem]:
    results: list[SearchItem] = []

    # Actors
    actor_stmt = select(Actor).where(Actor.canonical_name.ilike(f"%{payload.query}%")).limit(payload.limit)
    actor_res = await session.execute(actor_stmt)
    for a in actor_res.scalars():
        results.append(SearchItem(id=a.id, type="actor", title=a.canonical_name, detail=a.description))

    # Events
    event_stmt = select(Event).where(Event.title.ilike(f"%{payload.query}%")).limit(payload.limit)
    event_res = await session.execute(event_stmt)
    for e in event_res.scalars():
        results.append(SearchItem(id=e.id, type="event", title=e.title, detail=e.summary))

    # Claims
    claim_stmt = select(Claim).where(Claim.claim_text.ilike(f"%{payload.query}%")).limit(payload.limit)
    claim_res = await session.execute(claim_stmt)
    for c in claim_res.scalars():
        results.append(SearchItem(id=c.id, type="claim", title=c.claim_text, detail=c.normalized_claim))

    # Documents
    doc_stmt = select(Document).where(Document.title.ilike(f"%{payload.query}%")).limit(payload.limit)
    doc_res = await session.execute(doc_stmt)
    for d in doc_res.scalars():
        results.append(SearchItem(id=d.id, type="document", title=d.title, detail=d.canonical_url))

    return results[:payload.limit]


class EventInvestigationRequest(BaseModel):
    event_id: UUID
    priority: str = "medium"


@router.post("/event-investigation", status_code=201)
async def event_investigation(
    payload: EventInvestigationRequest,
    session: SessionDep,
    principal: ReadPrincipal,
) -> dict[str, object]:
    events_repo = EventRepository(session)
    event = await events_repo.get(payload.event_id)
    if not event:
        raise NotFoundError(f"Event {payload.event_id} not found")

    service = InvestigationService(session)
    investigation = await service.launch_investigation(
        title=f"Investigation: {event.title}",
        question=f"Analyze and verify event highlights and claims related to: {event.title}",
        requested_by=str(principal.user_id),
        priority=payload.priority,
    )
    return {
        "investigation_id": str(investigation.id),
        "status": investigation.status,
        "title": investigation.title,
    }


@router.post("/daily-brief", response_model=ReportOut, status_code=201)
async def daily_brief(
    session: SessionDep,
    principal: ReadPrincipal,
) -> ReportOut:
    generator = ReportGenerator(session)
    report = await generator.generate_daily_brief(
        llm=_try_get_llm(),
        triggered_by=str(principal.user_id),
    )
    return ReportOut.from_domain(report)


@router.post("/scenario-simulation", response_model=ScenarioUpdateRecommendation)
async def scenario_simulation(
    payload: ScenarioSimulationRequest,
    session: SessionDep,
    _principal: ReadPrincipal,
) -> ScenarioUpdateRecommendation:
    llm = _try_get_llm()
    if llm is None:
        raise LLMConfigurationError("Scenario simulation requires a configured LLM provider")

    result = await ScenarioEngine(session).simulate(
        scope_type=payload.scope_type,
        scope_id=payload.scope_id,
        scenario_family=payload.scenario_family,
        time_horizon=payload.time_horizon,
        hypothetical_context=payload.hypothetical_context,
        llm=llm,
    )
    return result

