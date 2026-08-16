from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from mei.domain.investigations.models import Investigation, InvestigationStep


class InvestigationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, investigation_id: UUID) -> Investigation | None:
        stmt = select(Investigation).where(Investigation.id == investigation_id)
        result = await self._session.execute(stmt)
        return result.scalars().first()

    async def list_all(
        self,
        *,
        status: str | None = None,
        priority: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Investigation]:
        stmt = select(Investigation).order_by(Investigation.created_at.desc())
        if status is not None:
            stmt = stmt.where(Investigation.status == status)
        if priority is not None:
            stmt = stmt.where(Investigation.priority == priority)
        stmt = stmt.limit(limit).offset(offset)
        result = await self._session.execute(stmt)
        return list(result.scalars())

    async def create(
        self,
        *,
        title: str,
        question: str,
        requested_by: str,
        priority: str = "medium",
        assigned_to: str | None = None,
    ) -> Investigation:
        investigation = Investigation(
            title=title,
            question=question,
            requested_by=requested_by,
            priority=priority,
            assigned_to=assigned_to,
            status="pending",
        )
        self._session.add(investigation)
        await self._session.flush()
        return investigation

    async def create_step(
        self,
        *,
        investigation_id: UUID,
        step_type: str,
        sequence: int,
        input_json: dict[str, object] | None = None,
    ) -> InvestigationStep:
        step = InvestigationStep(
            investigation_id=investigation_id,
            step_type=step_type,
            sequence=sequence,
            status="pending",
            input_json=input_json or {},
        )
        self._session.add(step)
        await self._session.flush()
        return step

    async def get_steps(self, investigation_id: UUID) -> list[InvestigationStep]:
        stmt = (
            select(InvestigationStep)
            .where(InvestigationStep.investigation_id == investigation_id)
            .order_by(InvestigationStep.sequence.asc())
        )
        result = await self._session.execute(stmt)
        return list(result.scalars())

    async def update(
        self,
        investigation: Investigation,
        *,
        title: str | None = None,
        hypothesis: str | None = None,
        priority: str | None = None,
        status: str | None = None,
    ) -> Investigation:
        if title is not None:
            investigation.title = title
        if hypothesis is not None:
            investigation.hypothesis = hypothesis
        if priority is not None:
            investigation.priority = priority
        if status is not None:
            investigation.status = status
        await self._session.flush()
        return investigation

    async def delete(self, investigation: Investigation) -> None:
        await self._session.delete(investigation)
        await self._session.flush()


__all__ = ["InvestigationRepository"]

