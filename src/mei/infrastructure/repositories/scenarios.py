from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from mei.domain.scenarios.models import Scenario, ScenarioAssessment
from mei.shared.enums import ScenarioFamily, ScenarioStatus, ScopeType


class ScenarioRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, scenario_id: UUID) -> Scenario | None:
        return await self._session.get(Scenario, scenario_id)

    async def get_by_family(
        self, *, scope_type: ScopeType, scope_id: UUID | None, scenario_family: ScenarioFamily
    ) -> Scenario | None:
        stmt = select(Scenario).where(
            Scenario.scope_type == scope_type,
            Scenario.scope_id == scope_id,
            Scenario.scenario_family == scenario_family,
        )
        result = await self._session.execute(stmt)
        return result.scalars().first()

    async def list_by_scope(
        self, *, scope_type: ScopeType, scope_id: UUID | None, status: ScenarioStatus | None = None
    ) -> list[Scenario]:
        stmt = select(Scenario).where(
            Scenario.scope_type == scope_type, Scenario.scope_id == scope_id
        )
        if status is not None:
            stmt = stmt.where(Scenario.status == status)
        stmt = stmt.order_by(Scenario.scenario_family)
        result = await self._session.execute(stmt)
        return list(result.scalars())

    async def list_all(
        self,
        *,
        status: ScenarioStatus | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Scenario]:
        stmt = select(Scenario).order_by(Scenario.created_at.desc())
        if status is not None:
            stmt = stmt.where(Scenario.status == status)
        stmt = stmt.limit(limit).offset(offset)
        result = await self._session.execute(stmt)
        return list(result.scalars())

    async def create(
        self,
        *,
        name: str,
        scope_type: ScopeType,
        scope_id: UUID | None,
        scenario_family: ScenarioFamily,
        time_horizon: str,
        description: str | None = None,
    ) -> Scenario:
        scenario = Scenario(
            name=name,
            scope_type=scope_type,
            scope_id=scope_id,
            scenario_family=scenario_family,
            time_horizon=time_horizon,
            description=description,
        )
        self._session.add(scenario)
        await self._session.flush()
        return scenario

    async def set_status(self, scenario_id: UUID, status: ScenarioStatus) -> None:
        scenario = await self.get(scenario_id)
        if scenario is not None:
            scenario.status = status
            await self._session.flush()

    async def get_latest_assessment(
        self, scenario_id: UUID, *, as_of: datetime | None = None
    ) -> ScenarioAssessment | None:
        stmt = select(ScenarioAssessment).where(ScenarioAssessment.scenario_id == scenario_id)
        if as_of is not None:
            stmt = stmt.where(ScenarioAssessment.assessed_at <= as_of)
        stmt = stmt.order_by(ScenarioAssessment.assessed_at.desc()).limit(1)
        result = await self._session.execute(stmt)
        return result.scalars().first()

    async def get_previous_assessment(
        self, scenario_id: UUID, *, before: datetime
    ) -> ScenarioAssessment | None:
        stmt = (
            select(ScenarioAssessment)
            .where(
                ScenarioAssessment.scenario_id == scenario_id,
                ScenarioAssessment.assessed_at < before,
            )
            .order_by(ScenarioAssessment.assessed_at.desc())
            .limit(1)
        )
        result = await self._session.execute(stmt)
        return result.scalars().first()

    async def list_assessments(
        self,
        scenario_id: UUID,
        *,
        since: datetime | None = None,
        until: datetime | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[ScenarioAssessment]:
        stmt = select(ScenarioAssessment).where(ScenarioAssessment.scenario_id == scenario_id)
        if since is not None:
            stmt = stmt.where(ScenarioAssessment.assessed_at >= since)
        if until is not None:
            stmt = stmt.where(ScenarioAssessment.assessed_at <= until)
        stmt = stmt.order_by(ScenarioAssessment.assessed_at.desc()).limit(limit).offset(offset)
        result = await self._session.execute(stmt)
        return list(result.scalars())

    async def create_assessment(
        self,
        *,
        scenario_id: UUID,
        assessed_at: datetime,
        probability_low: float,
        probability_high: float,
        confidence: float,
        assumptions: list[str],
        trigger_events: list[str],
        leading_indicators: list[str],
        expected_actor_behavior: str | None,
        military_consequences: str | None,
        economic_consequences: str | None,
        humanitarian_consequences: str | None,
        invalidation_criteria: list[str],
        explanation_of_change: str | None,
        evidence_bundle_id: UUID | None,
        model_version: str | None,
        approved_by: str | None,
        approved_at: datetime | None,
    ) -> ScenarioAssessment:
        assessment = ScenarioAssessment(
            scenario_id=scenario_id,
            assessed_at=assessed_at,
            probability_low=probability_low,
            probability_high=probability_high,
            confidence=confidence,
            assumptions_json=list(assumptions),
            trigger_events_json=list(trigger_events),
            leading_indicators_json=list(leading_indicators),
            expected_actor_behavior=expected_actor_behavior,
            military_consequences=military_consequences,
            economic_consequences=economic_consequences,
            humanitarian_consequences=humanitarian_consequences,
            invalidation_criteria_json=list(invalidation_criteria),
            explanation_of_change=explanation_of_change,
            evidence_bundle_id=evidence_bundle_id,
            model_version=model_version,
            approved_by=approved_by,
            approved_at=approved_at,
        )
        self._session.add(assessment)
        await self._session.flush()
        return assessment

    async def update(
        self,
        scenario: Scenario,
        *,
        name: str | None = None,
        scenario_family: ScenarioFamily | None = None,
        time_horizon: str | None = None,
        description: str | None = None,
        status: ScenarioStatus | None = None,
    ) -> Scenario:
        if name is not None:
            scenario.name = name
        if scenario_family is not None:
            scenario.scenario_family = scenario_family
        if time_horizon is not None:
            scenario.time_horizon = time_horizon
        if description is not None:
            scenario.description = description
        if status is not None:
            scenario.status = status
        await self._session.flush()
        return scenario

    async def delete(self, scenario: Scenario) -> None:
        await self._session.delete(scenario)
        await self._session.flush()


__all__ = ["ScenarioRepository"]

