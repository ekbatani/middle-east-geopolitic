"""Independent per-analyst positions and where they disagree (design doc section 35, Phase 6)."""

from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field

from apps.api.audit import audit
from apps.api.dependencies import SessionDep, require_scopes
from mei.application.services.analyst_disagreement import (
    DEFAULT_SCORE_SPREAD_THRESHOLD,
    AnalystDisagreementService,
)
from mei.domain.analyst_assessments.models import AnalystAssessment
from mei.infrastructure.auth.principal import Principal
from mei.shared.enums import DisagreementSubjectType, Scope

router = APIRouter(prefix="/analyst-assessments", tags=["analyst-assessments"])

ReadPrincipal = Annotated[Principal, Depends(require_scopes(Scope.INTELLIGENCE_READ))]
RecordPrincipal = Annotated[Principal, Depends(require_scopes(Scope.ANALYST_ASSESSMENTS_RECORD))]


class AnalystAssessmentOut(BaseModel):
    id: UUID
    subject_type: DisagreementSubjectType
    subject_id: UUID
    analyst_user_id: UUID | None
    stance: str | None
    score: float | None
    confidence: float | None
    rationale: str | None
    evidence_bundle_id: UUID | None
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_domain(cls, assessment: AnalystAssessment) -> "AnalystAssessmentOut":
        return cls(
            id=assessment.id,
            subject_type=assessment.subject_type,
            subject_id=assessment.subject_id,
            analyst_user_id=assessment.analyst_user_id,
            stance=assessment.stance,
            score=assessment.score,
            confidence=assessment.confidence,
            rationale=assessment.rationale,
            evidence_bundle_id=assessment.evidence_bundle_id,
            created_at=assessment.created_at,
            updated_at=assessment.updated_at,
        )


class RecordPositionRequest(BaseModel):
    subject_type: DisagreementSubjectType
    subject_id: UUID
    stance: str | None = None
    score: float | None = Field(default=None, ge=0, le=100)
    confidence: float | None = Field(default=None, ge=0, le=1)
    rationale: str | None = None
    evidence_bundle_id: UUID | None = None


class DisagreementSummaryOut(BaseModel):
    subject_type: DisagreementSubjectType
    subject_id: UUID
    position_count: int
    distinct_stances: int
    score_spread: float | None


@router.post("", response_model=AnalystAssessmentOut, status_code=201)
async def record_position(
    payload: RecordPositionRequest, session: SessionDep, principal: RecordPrincipal
) -> AnalystAssessmentOut:
    assessment = await AnalystDisagreementService(session).record_position(
        subject_type=payload.subject_type,
        subject_id=payload.subject_id,
        analyst_user_id=principal.user_id,
        stance=payload.stance,
        score=payload.score,
        confidence=payload.confidence,
        rationale=payload.rationale,
        evidence_bundle_id=payload.evidence_bundle_id,
    )
    await audit(
        session,
        principal,
        "analyst_assessment.recorded",
        resource_type="analyst_assessment",
        resource_id=str(assessment.id),
        metadata={
            "subject_type": str(payload.subject_type),
            "subject_id": str(payload.subject_id),
        },
    )
    return AnalystAssessmentOut.from_domain(assessment)


@router.get("", response_model=list[AnalystAssessmentOut])
async def list_positions(
    session: SessionDep,
    _principal: ReadPrincipal,
    subject_type: DisagreementSubjectType,
    subject_id: UUID,
) -> list[AnalystAssessmentOut]:
    positions = await AnalystDisagreementService(session).list_positions(
        subject_type=subject_type, subject_id=subject_id
    )
    return [AnalystAssessmentOut.from_domain(p) for p in positions]


@router.get("/disagreements", response_model=list[DisagreementSummaryOut])
async def list_disagreements(
    session: SessionDep,
    _principal: ReadPrincipal,
    subject_type: DisagreementSubjectType | None = None,
    score_spread_threshold: float = Query(default=DEFAULT_SCORE_SPREAD_THRESHOLD, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> list[DisagreementSummaryOut]:
    rows = await AnalystDisagreementService(session).list_disagreements(
        subject_type=subject_type,
        score_spread_threshold=score_spread_threshold,
        limit=limit,
        offset=offset,
    )
    return [
        DisagreementSummaryOut(
            subject_type=row[0],
            subject_id=row[1],
            position_count=row[2],
            distinct_stances=row[3],
            score_spread=row[4],
        )
        for row in rows
    ]
