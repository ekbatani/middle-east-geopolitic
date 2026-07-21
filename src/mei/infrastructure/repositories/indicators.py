from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from mei.domain.indicators.models import IndicatorDefinition, IndicatorObservation
from mei.shared.enums import IndicatorNormalizationMethod, ScopeType


class IndicatorRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_definition(self, indicator_id: UUID) -> IndicatorDefinition | None:
        return await self._session.get(IndicatorDefinition, indicator_id)

    async def get_definition_by_code(self, code: str) -> IndicatorDefinition | None:
        result = await self._session.execute(
            select(IndicatorDefinition).where(IndicatorDefinition.code == code)
        )
        return result.scalars().first()

    async def list_definitions(self, *, active_only: bool = True) -> list[IndicatorDefinition]:
        stmt = select(IndicatorDefinition).order_by(IndicatorDefinition.code)
        if active_only:
            stmt = stmt.where(IndicatorDefinition.active.is_(True))
        result = await self._session.execute(stmt)
        return list(result.scalars())

    async def create_definition(
        self,
        *,
        code: str,
        name: str,
        category: str,
        value_type: str,
        normalization_method: IndicatorNormalizationMethod = IndicatorNormalizationMethod.MIN_MAX,
        description: str | None = None,
        lower_bound: float | None = None,
        upper_bound: float | None = None,
        staleness_hours: int | None = None,
        default_weight: float | None = None,
        active: bool = True,
        ruleset_version: str = "v1",
    ) -> IndicatorDefinition:
        definition = IndicatorDefinition(
            code=code,
            name=name,
            description=description,
            category=category,
            value_type=value_type,
            normalization_method=normalization_method,
            lower_bound=lower_bound,
            upper_bound=upper_bound,
            staleness_hours=staleness_hours,
            default_weight=default_weight,
            active=active,
            ruleset_version=ruleset_version,
        )
        self._session.add(definition)
        await self._session.flush()
        return definition

    async def add_observation(
        self,
        *,
        indicator_id: UUID,
        scope_type: ScopeType,
        scope_id: UUID,
        observed_at: datetime,
        raw_value: float,
        normalized_value: float,
        confidence: float,
        evidence_bundle_id: UUID | None = None,
        source_method: str | None = None,
    ) -> IndicatorObservation:
        observation = IndicatorObservation(
            indicator_id=indicator_id,
            scope_type=scope_type,
            scope_id=scope_id,
            observed_at=observed_at,
            raw_value=raw_value,
            normalized_value=normalized_value,
            confidence=confidence,
            evidence_bundle_id=evidence_bundle_id,
            source_method=source_method,
        )
        self._session.add(observation)
        await self._session.flush()
        return observation

    async def get_latest_observation(
        self,
        *,
        indicator_id: UUID,
        scope_type: ScopeType,
        scope_id: UUID,
        as_of: datetime | None = None,
    ) -> IndicatorObservation | None:
        stmt = select(IndicatorObservation).where(
            IndicatorObservation.indicator_id == indicator_id,
            IndicatorObservation.scope_type == scope_type,
            IndicatorObservation.scope_id == scope_id,
        )
        if as_of is not None:
            stmt = stmt.where(IndicatorObservation.observed_at <= as_of)
        stmt = stmt.order_by(IndicatorObservation.observed_at.desc()).limit(1)
        result = await self._session.execute(stmt)
        return result.scalars().first()

    async def list_observations(
        self,
        *,
        indicator_id: UUID,
        scope_type: ScopeType,
        scope_id: UUID,
        limit: int = 100,
    ) -> list[IndicatorObservation]:
        stmt = (
            select(IndicatorObservation)
            .where(
                IndicatorObservation.indicator_id == indicator_id,
                IndicatorObservation.scope_type == scope_type,
                IndicatorObservation.scope_id == scope_id,
            )
            .order_by(IndicatorObservation.observed_at.desc())
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars())


__all__ = ["IndicatorRepository"]
