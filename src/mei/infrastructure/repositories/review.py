from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from mei.domain.review.models import ReviewItem
from mei.shared.enums import ReviewStatus, ReviewType


class ReviewRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, item_id: UUID) -> ReviewItem | None:
        return await self._session.get(ReviewItem, item_id)

    async def list_all(
        self,
        *,
        review_type: ReviewType | None = None,
        status: ReviewStatus | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[ReviewItem]:
        stmt = select(ReviewItem).order_by(ReviewItem.created_at.desc())
        if review_type is not None:
            stmt = stmt.where(ReviewItem.review_type == review_type)
        if status is not None:
            stmt = stmt.where(ReviewItem.status == status)
        stmt = stmt.limit(limit).offset(offset)
        result = await self._session.execute(stmt)
        return list(result.scalars())

    async def create(
        self,
        *,
        review_type: ReviewType,
        subject: dict[str, object],
        candidates: list[object],
    ) -> ReviewItem:
        item = ReviewItem(
            review_type=review_type,
            status=ReviewStatus.PENDING,
            subject_json=subject,
            candidates_json=candidates,
        )
        self._session.add(item)
        await self._session.flush()
        return item

    async def resolve(
        self,
        item: ReviewItem,
        *,
        status: ReviewStatus,
        resolution: dict[str, object],
        resolved_by: str,
        resolved_at: datetime,
    ) -> None:
        item.status = status
        item.resolution_json = resolution
        item.resolved_by = resolved_by
        item.resolved_at = resolved_at
        await self._session.flush()


__all__ = ["ReviewRepository"]
