from datetime import datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from mei.domain.indicators.models import IndicatorDefinition, IndicatorObservation
from mei.infrastructure.repositories.indicators import IndicatorRepository
from mei.shared.enums import IndicatorNormalizationMethod, ScopeType
from mei.shared.errors import NotFoundError, ValidationError
from mei.shared.time import utcnow


def normalize_value(
    raw_value: float,
    *,
    method: IndicatorNormalizationMethod,
    lower_bound: float | None,
    upper_bound: float | None,
) -> float:
    """Map a raw indicator reading onto the 0-1 scale the risk engine consumes.

    Design doc section 18.2: every indicator defines "source value;
    normalization method; ... upper and lower bounds". The result is always
    clamped to `[0, 1]` so a single out-of-range or misconfigured reading
    can't blow up a downstream weighted sum past its expected range.
    """
    if method is IndicatorNormalizationMethod.BOOLEAN:
        return 1.0 if raw_value != 0 else 0.0

    if method is IndicatorNormalizationMethod.MANUAL:
        return max(0.0, min(1.0, raw_value))

    if method is IndicatorNormalizationMethod.MIN_MAX:
        if lower_bound is None or upper_bound is None:
            raise ValidationError("min_max normalization requires both lower_bound and upper_bound")
        if upper_bound == lower_bound:
            raise ValidationError("upper_bound must differ from lower_bound")
        scaled = (raw_value - lower_bound) / (upper_bound - lower_bound)
        return max(0.0, min(1.0, scaled))

    raise ValidationError(f"Unsupported normalization method: {method}")


class IndicatorService:
    def __init__(self, session: AsyncSession) -> None:
        self._indicators = IndicatorRepository(session)

    async def record_observation(
        self,
        *,
        indicator_code: str,
        scope_type: ScopeType,
        scope_id: UUID,
        raw_value: float,
        confidence: float = 1.0,
        observed_at: datetime | None = None,
        evidence_bundle_id: UUID | None = None,
        source_method: str | None = None,
    ) -> IndicatorObservation:
        definition = await self._indicators.get_definition_by_code(indicator_code)
        if definition is None:
            raise NotFoundError(f"Indicator '{indicator_code}' not found")

        normalized_value = normalize_value(
            raw_value,
            method=definition.normalization_method,
            lower_bound=definition.lower_bound,
            upper_bound=definition.upper_bound,
        )

        return await self._indicators.add_observation(
            indicator_id=definition.id,
            scope_type=scope_type,
            scope_id=scope_id,
            observed_at=observed_at or utcnow(),
            raw_value=raw_value,
            normalized_value=normalized_value,
            confidence=max(0.0, min(1.0, confidence)),
            evidence_bundle_id=evidence_bundle_id,
            source_method=source_method,
        )

    async def get_definition_by_code(self, code: str) -> IndicatorDefinition | None:
        return await self._indicators.get_definition_by_code(code)


__all__ = ["IndicatorService", "normalize_value"]
