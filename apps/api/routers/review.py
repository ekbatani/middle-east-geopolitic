from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, ConfigDict

from apps.api.audit import audit
from apps.api.dependencies import SessionDep, require_scopes
from mei.application.services.review import ReviewService
from mei.infrastructure.auth.principal import Principal
from mei.shared.enums import ReviewStatus, ReviewType, Scope

router = APIRouter(prefix="/review-items", tags=["review"])

ReadPrincipal = Annotated[Principal, Depends(require_scopes(Scope.INTELLIGENCE_READ))]
ResolvePrincipal = Annotated[Principal, Depends(require_scopes(Scope.REVIEW_RESOLVE))]


class ReviewItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    review_type: ReviewType
    status: ReviewStatus
    subject_json: dict[str, object]
    candidates_json: list[object]
    resolution_json: dict[str, object] | None
    created_at: datetime
    resolved_at: datetime | None
    resolved_by: str | None


class ResolveReviewItemRequest(BaseModel):
    resolved_actor_id: UUID


class AcknowledgeReviewItemRequest(BaseModel):
    note: str | None = None


@router.get("", response_model=list[ReviewItemOut])
async def list_review_items(
    session: SessionDep,
    _principal: ReadPrincipal,
    review_type: ReviewType | None = None,
    status: ReviewStatus | None = ReviewStatus.PENDING,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> list[ReviewItemOut]:
    items = await ReviewService(session).list_pending(
        review_type=review_type, status=status, limit=limit, offset=offset
    )
    return [ReviewItemOut.model_validate(item) for item in items]


@router.get("/{item_id}", response_model=ReviewItemOut)
async def get_review_item(
    item_id: UUID, session: SessionDep, _principal: ReadPrincipal
) -> ReviewItemOut:
    item = await ReviewService(session).get(item_id)
    return ReviewItemOut.model_validate(item)


@router.post("/{item_id}/resolve", response_model=ReviewItemOut)
async def resolve_review_item(
    item_id: UUID,
    payload: ResolveReviewItemRequest,
    session: SessionDep,
    principal: ResolvePrincipal,
) -> ReviewItemOut:
    item = await ReviewService(session).resolve_entity_resolution(
        item_id, resolved_actor_id=payload.resolved_actor_id, principal=principal
    )
    await audit(
        session,
        principal,
        "review_item.resolved",
        resource_type="review_item",
        resource_id=str(item_id),
        metadata={"resolved_actor_id": str(payload.resolved_actor_id)},
    )
    return ReviewItemOut.model_validate(item)


@router.post("/{item_id}/acknowledge", response_model=ReviewItemOut)
async def acknowledge_review_item(
    item_id: UUID,
    payload: AcknowledgeReviewItemRequest,
    session: SessionDep,
    principal: ResolvePrincipal,
) -> ReviewItemOut:
    item = await ReviewService(session).acknowledge_high_impact_event(
        item_id, principal=principal, note=payload.note
    )
    await audit(
        session,
        principal,
        "review_item.acknowledged",
        resource_type="review_item",
        resource_id=str(item_id),
    )
    return ReviewItemOut.model_validate(item)


@router.post("/{item_id}/reject", response_model=ReviewItemOut)
async def reject_review_item(
    item_id: UUID, session: SessionDep, principal: ResolvePrincipal
) -> ReviewItemOut:
    item = await ReviewService(session).reject(item_id, principal=principal)
    await audit(
        session,
        principal,
        "review_item.rejected",
        resource_type="review_item",
        resource_id=str(item_id),
    )
    return ReviewItemOut.model_validate(item)
