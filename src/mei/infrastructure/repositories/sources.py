from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from mei.domain.sources.models import Source, SourceEndpoint
from mei.shared.enums import EndpointType, SourceType


class SourceRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, source_id: UUID) -> Source | None:
        result = await self._session.execute(
            select(Source).where(Source.id == source_id).options(selectinload(Source.endpoints))
        )
        return result.scalar_one_or_none()

    async def list_all(self, *, limit: int = 50, offset: int = 0) -> list[Source]:
        stmt = (
            select(Source)
            .options(selectinload(Source.endpoints))
            .order_by(Source.name)
            .limit(limit)
            .offset(offset)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().unique())

    async def get_by_base_url(self, base_url: str) -> Source | None:
        result = await self._session.execute(select(Source).where(Source.base_url == base_url))
        return result.scalar_one_or_none()

    async def list_endpoints_due(
        self, *, endpoint_type: EndpointType, schedule: str
    ) -> list[SourceEndpoint]:
        """Enabled endpoints of the given type/schedule tier, for the collector.

        `schedule` matches the `critical`/`normal` tiering seeded onto
        `SourceEndpoint.schedule` (design doc section 24.1's two collection
        frequencies), joined against the parent source's `enabled` flag.
        """
        stmt = (
            select(SourceEndpoint)
            .join(Source, Source.id == SourceEndpoint.source_id)
            .where(
                SourceEndpoint.endpoint_type == endpoint_type,
                SourceEndpoint.schedule == schedule,
                Source.enabled.is_(True),
            )
        )
        result = await self._session.execute(stmt)
        return list(result.scalars())

    async def list_failing_endpoints(self, *, min_failure_count: int = 1) -> list[SourceEndpoint]:
        stmt = select(SourceEndpoint).where(SourceEndpoint.failure_count >= min_failure_count)
        result = await self._session.execute(stmt)
        return list(result.scalars())

    async def create(
        self,
        *,
        name: str,
        source_type: SourceType,
        base_url: str | None = None,
        default_language: str | None = None,
    ) -> Source:
        source = Source(
            name=name,
            source_type=source_type,
            base_url=base_url,
            default_language=default_language,
        )
        self._session.add(source)
        await self._session.flush()
        return source

    async def create_endpoint(
        self,
        *,
        source_id: UUID,
        endpoint_type: EndpointType,
        url: str,
        parser_name: str | None = None,
        schedule: str | None = None,
        priority: int = 100,
    ) -> SourceEndpoint:
        endpoint = SourceEndpoint(
            source_id=source_id,
            endpoint_type=endpoint_type,
            url=url,
            parser_name=parser_name,
            schedule=schedule,
            priority=priority,
        )
        self._session.add(endpoint)
        await self._session.flush()
        return endpoint

    async def get_endpoint(self, endpoint_id: UUID) -> SourceEndpoint | None:
        return await self._session.get(SourceEndpoint, endpoint_id)

    async def mark_endpoint_success(self, endpoint: SourceEndpoint, *, at: datetime) -> None:
        endpoint.last_success_at = at
        endpoint.failure_count = 0
        await self._session.flush()

    async def mark_endpoint_failure(self, endpoint: SourceEndpoint, *, at: datetime) -> None:
        endpoint.last_failure_at = at
        endpoint.failure_count += 1
        await self._session.flush()


__all__ = ["SourceRepository"]
