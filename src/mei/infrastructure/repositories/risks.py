from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from mei.domain.risks.models import RiskAssessment, RiskDefinition, RiskIndicatorWeight
from mei.shared.enums import IndicatorDirection, RiskApprovalStatus, ScopeType, Trend


class RiskRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_definition(self, risk_definition_id: UUID) -> RiskDefinition | None:
        return await self._session.get(RiskDefinition, risk_definition_id)

    async def get_definition_by_code(self, code: str) -> RiskDefinition | None:
        result = await self._session.execute(
            select(RiskDefinition).where(RiskDefinition.code == code)
        )
        return result.scalars().first()

    async def list_definitions(self) -> list[RiskDefinition]:
        result = await self._session.execute(select(RiskDefinition).order_by(RiskDefinition.code))
        return list(result.scalars())

    async def create_definition(
        self,
        *,
        code: str,
        name: str,
        scope_types: list[str],
        description: str | None = None,
        ruleset_version: str = "v1",
    ) -> RiskDefinition:
        definition = RiskDefinition(
            code=code,
            name=name,
            description=description,
            scope_types=scope_types,
            ruleset_version=ruleset_version,
        )
        self._session.add(definition)
        await self._session.flush()
        return definition

    async def set_weight(
        self,
        *,
        risk_definition_id: UUID,
        indicator_definition_id: UUID,
        weight: float,
        direction: IndicatorDirection = IndicatorDirection.POSITIVE,
        conditions: dict[str, object] | None = None,
    ) -> RiskIndicatorWeight:
        existing = await self._session.get(
            RiskIndicatorWeight, (risk_definition_id, indicator_definition_id)
        )
        if existing is not None:
            existing.weight = weight
            existing.direction = direction
            existing.conditions_json = conditions or {}
            await self._session.flush()
            return existing

        link = RiskIndicatorWeight(
            risk_definition_id=risk_definition_id,
            indicator_definition_id=indicator_definition_id,
            weight=weight,
            direction=direction,
            conditions_json=conditions or {},
        )
        self._session.add(link)
        await self._session.flush()
        return link

    async def list_weights(self, risk_definition_id: UUID) -> list[RiskIndicatorWeight]:
        result = await self._session.execute(
            select(RiskIndicatorWeight).where(
                RiskIndicatorWeight.risk_definition_id == risk_definition_id
            )
        )
        return list(result.scalars())

    async def get_assessment(self, assessment_id: UUID) -> RiskAssessment | None:
        return await self._session.get(RiskAssessment, assessment_id)

    async def get_latest_assessment(
        self,
        *,
        risk_definition_id: UUID,
        scope_type: ScopeType,
        scope_id: UUID | None,
        as_of: datetime | None = None,
    ) -> RiskAssessment | None:
        stmt = select(RiskAssessment).where(
            RiskAssessment.risk_definition_id == risk_definition_id,
            RiskAssessment.scope_type == scope_type,
            RiskAssessment.scope_id == scope_id,
        )
        if as_of is not None:
            stmt = stmt.where(RiskAssessment.assessed_at <= as_of)
        stmt = stmt.order_by(RiskAssessment.assessed_at.desc()).limit(1)
        result = await self._session.execute(stmt)
        return result.scalars().first()

    async def get_previous_assessment(
        self,
        *,
        risk_definition_id: UUID,
        scope_type: ScopeType,
        scope_id: UUID | None,
        before: datetime,
    ) -> RiskAssessment | None:
        stmt = (
            select(RiskAssessment)
            .where(
                RiskAssessment.risk_definition_id == risk_definition_id,
                RiskAssessment.scope_type == scope_type,
                RiskAssessment.scope_id == scope_id,
                RiskAssessment.assessed_at < before,
            )
            .order_by(RiskAssessment.assessed_at.desc())
            .limit(1)
        )
        result = await self._session.execute(stmt)
        return result.scalars().first()

    async def list_history(
        self,
        *,
        risk_definition_id: UUID,
        scope_type: ScopeType,
        scope_id: UUID | None,
        since: datetime | None = None,
        until: datetime | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[RiskAssessment]:
        stmt = select(RiskAssessment).where(
            RiskAssessment.risk_definition_id == risk_definition_id,
            RiskAssessment.scope_type == scope_type,
            RiskAssessment.scope_id == scope_id,
        )
        if since is not None:
            stmt = stmt.where(RiskAssessment.assessed_at >= since)
        if until is not None:
            stmt = stmt.where(RiskAssessment.assessed_at <= until)
        stmt = stmt.order_by(RiskAssessment.assessed_at.desc()).limit(limit).offset(offset)
        result = await self._session.execute(stmt)
        return list(result.scalars())

    async def list_recent_assessments(
        self, *, since: datetime, limit: int = 200
    ) -> list[RiskAssessment]:
        """Every assessment recorded since `since`, across all definitions and
        scopes, for report generation's "material changes" section (design
        doc section 25.1 step 5). Unlike `list_history`, this isn't scoped to
        one definition/scope pair."""
        stmt = (
            select(RiskAssessment)
            .where(RiskAssessment.assessed_at >= since)
            .order_by(RiskAssessment.assessed_at.desc())
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars())

    async def create_assessment(
        self,
        *,
        risk_definition_id: UUID,
        scope_type: ScopeType,
        scope_id: UUID | None,
        assessed_at: datetime,
        base_score: int,
        llm_adjustment: int,
        final_score: int,
        previous_score: int | None,
        trend: Trend | None,
        confidence: float,
        explanation: str | None,
        counter_indicators: list[str],
        contributions: list[object],
        evidence_bundle_id: UUID | None,
        ruleset_version: str,
        model_version: str | None,
        approval_status: RiskApprovalStatus,
        approved_by: str | None,
        approved_at: datetime | None,
    ) -> RiskAssessment:
        assessment = RiskAssessment(
            risk_definition_id=risk_definition_id,
            scope_type=scope_type,
            scope_id=scope_id,
            assessed_at=assessed_at,
            base_score=base_score,
            llm_adjustment=llm_adjustment,
            final_score=final_score,
            previous_score=previous_score,
            trend=trend,
            confidence=confidence,
            explanation=explanation,
            counter_indicators_json=counter_indicators,
            contributions_json=contributions,
            evidence_bundle_id=evidence_bundle_id,
            ruleset_version=ruleset_version,
            model_version=model_version,
            approval_status=approval_status,
            approved_by=approved_by,
            approved_at=approved_at,
        )
        self._session.add(assessment)
        await self._session.flush()
        return assessment


__all__ = ["RiskRepository"]
