"""Multi-model review results for high-impact risk assessments (design doc section 35, Phase 6)."""

from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from apps.api.dependencies import SessionDep, require_scopes
from mei.domain.model_reviews.models import ModelReviewResult
from mei.infrastructure.auth.principal import Principal
from mei.infrastructure.repositories.model_reviews import ModelReviewRepository
from mei.shared.enums import ModelReviewSubjectType, Scope
from mei.shared.errors import NotFoundError

router = APIRouter(prefix="/model-reviews", tags=["model-reviews"])

ReadPrincipal = Annotated[Principal, Depends(require_scopes(Scope.INTELLIGENCE_READ))]


class ModelReviewResultOut(BaseModel):
    id: UUID
    subject_type: ModelReviewSubjectType
    subject_id: UUID
    trigger_reason: str
    primary_model: str
    secondary_model: str
    primary_final_score: int
    secondary_final_score: int
    agreement: bool | None
    agreement_delta: int | None
    secondary_output_json: dict[str, object]
    reviewed_at: datetime

    @classmethod
    def from_domain(cls, review: ModelReviewResult) -> "ModelReviewResultOut":
        return cls(
            id=review.id,
            subject_type=review.subject_type,
            subject_id=review.subject_id,
            trigger_reason=review.trigger_reason,
            primary_model=review.primary_model,
            secondary_model=review.secondary_model,
            primary_final_score=review.primary_final_score,
            secondary_final_score=review.secondary_final_score,
            agreement=review.agreement,
            agreement_delta=review.agreement_delta,
            secondary_output_json=review.secondary_output_json,
            reviewed_at=review.reviewed_at,
        )


@router.get("", response_model=list[ModelReviewResultOut])
async def list_model_reviews(
    session: SessionDep,
    _principal: ReadPrincipal,
    subject_type: ModelReviewSubjectType | None = None,
    agreement: bool | None = None,
    since: datetime | None = None,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> list[ModelReviewResultOut]:
    reviews = await ModelReviewRepository(session).list_all(
        subject_type=subject_type, agreement=agreement, since=since, limit=limit, offset=offset
    )
    return [ModelReviewResultOut.from_domain(r) for r in reviews]


@router.get("/{review_id}", response_model=ModelReviewResultOut)
async def get_model_review(
    review_id: UUID, session: SessionDep, _principal: ReadPrincipal
) -> ModelReviewResultOut:
    review = await ModelReviewRepository(session).get(review_id)
    if review is None:
        raise NotFoundError(f"Model review {review_id} not found")
    return ModelReviewResultOut.from_domain(review)
