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
        stmt = select(Source).where(Source.base_url == base_url).limit(1)
        result = await self._session.execute(stmt)
        return result.scalars().first()

    async def get_by_name(self, name: str) -> Source | None:
        stmt = select(Source).where(Source.name == name).limit(1)
        result = await self._session.execute(stmt)
        return result.scalars().first()

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


    async def update(
        self,
        source: Source,
        *,
        name: str | None = None,
        source_type: SourceType | None = None,
        base_url: str | None = None,
        default_language: str | None = None,
        enabled: bool | None = None,
    ) -> Source:
        if name is not None:
            source.name = name
        if source_type is not None:
            source.source_type = source_type
        if base_url is not None:
            source.base_url = base_url
        if default_language is not None:
            source.default_language = default_language
        if enabled is not None:
            source.enabled = enabled
        await self._session.flush()
        return source

    async def delete(self, source: Source) -> None:
        await self._session.delete(source)
        await self._session.flush()

    async def update_endpoint(
        self,
        endpoint: SourceEndpoint,
        *,
        endpoint_type: EndpointType | None = None,
        url: str | None = None,
        schedule: str | None = None,
        priority: int | None = None,
    ) -> SourceEndpoint:
        if endpoint_type is not None:
            endpoint.endpoint_type = endpoint_type
        if url is not None:
            endpoint.url = url
        if schedule is not None:
            endpoint.schedule = schedule
        if priority is not None:
            endpoint.priority = priority
        await self._session.flush()
        return endpoint

    async def delete_endpoint(self, endpoint: SourceEndpoint) -> None:
        await self._session.delete(endpoint)
        await self._session.flush()


__all__ = ["SourceRepository"]

