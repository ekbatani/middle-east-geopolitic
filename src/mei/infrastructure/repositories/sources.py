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
    ) -> SourceEndpoint:
        endpoint = SourceEndpoint(
            source_id=source_id, endpoint_type=endpoint_type, url=url, parser_name=parser_name
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
