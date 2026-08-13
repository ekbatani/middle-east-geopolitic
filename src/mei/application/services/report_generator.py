"""Report generation (design doc section 25).

`ReportGenerator.generate` implements section 25.1's process: resolve
scope and period, pull approved records for that window, calculate
material changes, draft the narrative sections (LLM-optional, with a
plain deterministic fallback when none is configured), render Markdown,
and persist both the rendered content and an archived copy in object
storage.

Only the subset of section 25.3's daily-brief sections backed by data this
platform actually models is included here: executive assessment, event
highlights, risk-score changes, relationship-observation changes, and
active-scenario changes. Sections like "energy and maritime developments"
or "disputed and unresolved claims" would need dedicated domain
categorization this phase doesn't add — leaving them out is a scope
decision, not an oversight.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from functools import lru_cache
from pathlib import Path
from typing import NamedTuple
from uuid import UUID

import yaml
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from mei.domain.events.models import Event
from mei.domain.relationships.models import RelationshipObservation
from mei.domain.reports.models import Report
from mei.domain.risks.models import RiskAssessment
from mei.infrastructure.llm.protocol import StructuredLLM
from mei.infrastructure.object_storage_mock import ObjectStorage
from mei.infrastructure.repositories.events import EventRepository
from mei.infrastructure.repositories.relationships import RelationshipRepository
from mei.infrastructure.repositories.reports import ReportRepository
from mei.infrastructure.repositories.risks import RiskRepository
from mei.infrastructure.repositories.scenarios import ScenarioRepository
from mei.shared.config import get_settings
from mei.shared.enums import LifecycleStatus, ReportStatus, ReportType, ScenarioStatus, ScopeType
from mei.shared.errors import (
    ConflictError,
    LLMConfigurationError,
    LLMOutputError,
    NotFoundError,
    ValidationError,
)
from mei.shared.logging import get_logger
from mei.shared.time import utcnow

logger = get_logger(__name__)

PROMPT_TASK_NAME = "report_brief"
PROMPT_VERSION = "report_brief_v1"

_SCOPED_REPORT_TYPES = (ReportType.COUNTRY_BRIEF, ReportType.CONFLICT_BRIEF)

_REPO_ROOT = Path(__file__).resolve().parents[4]
_REPORT_TEMPLATES_PATH = _REPO_ROOT / "configs" / "report-templates.yml"


class ReportTemplate(NamedTuple):
    title: str
    period_days: int


@lru_cache
def _load_templates() -> dict[ReportType, ReportTemplate]:
    raw = yaml.safe_load(_REPORT_TEMPLATES_PATH.read_text(encoding="utf-8"))
    return {
        ReportType(entry["report_type"]): ReportTemplate(
            title=entry["title"], period_days=entry["period_days"]
        )
        for entry in raw["templates"]
    }


class ReportDraft(BaseModel):
    """Design doc section 25.1 step 6 ("generate structured report
    sections"), scoped to the subset of section 25.3 this phase supports."""

    executive_assessment: str = ""
    indicators_to_monitor: list[str] = Field(default_factory=list)


class ReportGenerator:
    def __init__(self, session: AsyncSession) -> None:
        self._reports = ReportRepository(session)
        self._events = EventRepository(session)
        self._risks = RiskRepository(session)
        self._relationships = RelationshipRepository(session)
        self._scenarios = ScenarioRepository(session)

    async def generate_daily_brief(
        self, *, llm: StructuredLLM | None = None, triggered_by: str | None = None
    ) -> Report:
        return await self.generate(ReportType.DAILY_BRIEF, llm=llm, triggered_by=triggered_by)

    async def generate_weekly_outlook(
        self, *, llm: StructuredLLM | None = None, triggered_by: str | None = None
    ) -> Report:
        return await self.generate(ReportType.WEEKLY_OUTLOOK, llm=llm, triggered_by=triggered_by)

    async def generate(
        self,
        report_type: ReportType,
        *,
        scope_type: ScopeType | None = None,
        scope_id: UUID | None = None,
        llm: StructuredLLM | None = None,
        triggered_by: str | None = None,
        as_of: datetime | None = None,
    ) -> Report:
        if report_type in _SCOPED_REPORT_TYPES and scope_id is None:
            raise ValidationError(f"Report type '{report_type}' requires a scope_id")

        template = _load_templates()[report_type]
        now = as_of or utcnow()
        period_start = now - timedelta(days=template.period_days)

        events = await self._events.list_all(
            lifecycle_status=LifecycleStatus.APPROVED, since=period_start, until=now, limit=100
        )
        risk_changes = [
            a
            for a in await self._risks.list_recent_assessments(since=period_start, limit=200)
            if a.trend is not None and a.trend.value != "stable"
        ]
        relationship_changes = [
            o
            for o in await self._relationships.list_recent_observations(
                since=period_start, limit=200
            )
            if o.trend is not None and o.trend.value != "stable"
        ]
        scenario_lines = await self._active_scenario_lines(as_of=now)

        draft = await self._draft_sections(
            llm,
            report_type=report_type,
            events=events,
            risk_changes=risk_changes,
            relationship_changes=relationship_changes,
            scenario_lines=scenario_lines,
        )

        content = self._render_markdown(
            title=template.title,
            period_start=period_start,
            period_end=now,
            events=events,
            risk_changes=risk_changes,
            relationship_changes=relationship_changes,
            scenario_lines=scenario_lines,
            draft=draft,
        )

        object_key = await self._archive(report_type=report_type, generated_at=now, content=content)

        model_version = None
        if llm is not None:
            settings = get_settings()
            model_version = f"{settings.llm_provider}:{settings.llm_model}:{PROMPT_VERSION}"

        report = await self._reports.create(
            report_type=report_type,
            title=template.title,
            scope_type=scope_type,
            scope_id=scope_id,
            period_start=period_start.date(),
            period_end=now.date(),
            content_markdown=content,
            content_object_key=object_key,
            generated_by_model=model_version,
            prompt_version=PROMPT_VERSION if llm is not None else None,
        )
        logger.info(
            "report_generator.generated",
            report_id=str(report.id),
            report_type=str(report_type),
            triggered_by=triggered_by or "system",
        )
        return report

    async def _active_scenario_lines(self, *, as_of: datetime) -> list[str]:
        lines: list[str] = []
        for scenario in await self._scenarios.list_all(status=ScenarioStatus.ACTIVE, limit=200):
            latest = await self._scenarios.get_latest_assessment(scenario.id, as_of=as_of)
            if latest is None:
                continue
            lines.append(
                f"- {scenario.name} ({scenario.scenario_family}): "
                f"{latest.probability_low:.0f}-{latest.probability_high:.0f}% "
                f"(confidence {latest.confidence:.2f})"
            )
        return lines

    async def _draft_sections(
        self,
        llm: StructuredLLM | None,
        *,
        report_type: ReportType,
        events: list[Event],
        risk_changes: list[RiskAssessment],
        relationship_changes: list[RelationshipObservation],
        scenario_lines: list[str],
    ) -> ReportDraft:
        if llm is None:
            return ReportDraft(
                executive_assessment=(
                    "No executive assessment drafted: no LLM is configured for this run."
                )
            )

        input_text = self._build_input_text(
            events=events,
            risk_changes=risk_changes,
            relationship_changes=relationship_changes,
            scenario_lines=scenario_lines,
        )
        try:
            return await llm.generate_structured(
                task_name=PROMPT_TASK_NAME,
                prompt_version=PROMPT_VERSION,
                input_text=input_text,
                output_model=ReportDraft,
                metadata={"report_type": str(report_type)},
            )
        except (LLMConfigurationError, LLMOutputError) as exc:
            logger.warning(
                "report_generator.draft_skipped", report_type=str(report_type), error=str(exc)
            )
            return ReportDraft(
                executive_assessment="No executive assessment drafted: LLM drafting failed."
            )

    @staticmethod
    def _build_input_text(
        *,
        events: list[Event],
        risk_changes: list[RiskAssessment],
        relationship_changes: list[RelationshipObservation],
        scenario_lines: list[str],
    ) -> str:
        lines = ["Approved events in the period:"]
        if events:
            lines.extend(f"- {e.started_at.isoformat()} {e.event_type}: {e.title}" for e in events)
        else:
            lines.append("- none")

        lines.append("Material risk-score changes in the period:")
        if risk_changes:
            lines.extend(
                f"- risk_definition {r.risk_definition_id}: "
                f"{r.previous_score if r.previous_score is not None else 'n/a'} -> "
                f"{r.final_score} ({r.trend})"
                for r in risk_changes
            )
        else:
            lines.append("- none")

        lines.append("Material relationship-observation changes in the period:")
        if relationship_changes:
            lines.extend(
                f"- relationship {o.relationship_id}: "
                f"escalation_risk={o.escalation_risk_score} ({o.trend})"
                for o in relationship_changes
            )
        else:
            lines.append("- none")

        lines.append("Active scenarios:")
        lines.extend(scenario_lines if scenario_lines else ["- none"])

        return "\n".join(lines)

    @staticmethod
    def _render_markdown(
        *,
        title: str,
        period_start: datetime,
        period_end: datetime,
        events: list[Event],
        risk_changes: list[RiskAssessment],
        relationship_changes: list[RelationshipObservation],
        scenario_lines: list[str],
        draft: ReportDraft,
    ) -> str:
        lines = [
            f"# {title}",
            f"Period: {period_start.date().isoformat()} to {period_end.date().isoformat()}",
            "",
            "## Executive assessment",
            draft.executive_assessment or "No material executive assessment available.",
            "",
            "## Event highlights",
        ]
        if events:
            lines.extend(
                f"- {e.started_at.isoformat()} — {e.title} (evidence: event/{e.id})" for e in events
            )
        else:
            lines.append("- No approved events in this period.")

        lines.extend(["", "## Risk-score changes"])
        if risk_changes:
            lines.extend(
                f"- risk_assessment/{r.id}: "
                f"{r.previous_score if r.previous_score is not None else 'n/a'} -> "
                f"{r.final_score} ({r.trend})"
                for r in risk_changes
            )
        else:
            lines.append("- No material risk-score changes in this period.")

        lines.extend(["", "## Relationship changes"])
        if relationship_changes:
            lines.extend(
                f"- relationship_observation/{o.id}: "
                f"escalation_risk={o.escalation_risk_score} ({o.trend})"
                for o in relationship_changes
            )
        else:
            lines.append("- No material relationship changes in this period.")

        lines.extend(["", "## Scenario changes"])
        lines.extend(scenario_lines if scenario_lines else ["- No active scenarios."])

        lines.extend(["", "## Indicators to monitor"])
        if draft.indicators_to_monitor:
            lines.extend(f"- {indicator}" for indicator in draft.indicators_to_monitor)
        else:
            lines.append("- None flagged.")

        return "\n".join(lines) + "\n"

    @staticmethod
    async def _archive(
        *, report_type: ReportType, generated_at: datetime, content: str
    ) -> str | None:
        key = f"reports/{generated_at:%Y/%m/%d}/{report_type}-{generated_at:%H%M%S}.md"
        try:
            storage = ObjectStorage()
            await storage.ensure_bucket()
            await storage.put_bytes(key, content.encode("utf-8"), content_type="text/markdown")
            return key
        except Exception as exc:
            logger.warning("report_generator.archive_failed", key=key, error=str(exc))
            return None

    async def approve_report(self, report_id: UUID, *, approved_by: str) -> Report:
        approved = await self._reports.approve(
            report_id, approved_by=approved_by, approved_at=utcnow()
        )
        if approved is None:
            raise NotFoundError(f"Report {report_id} not found")
        return approved

    async def reject_report(self, report_id: UUID) -> Report:
        report = await self._reports.reject(report_id)
        if report is None:
            raise NotFoundError(f"Report {report_id} not found")
        return report

    async def publish_report(self, report_id: UUID) -> Report:
        report = await self._reports.get(report_id)
        if report is None:
            raise NotFoundError(f"Report {report_id} not found")
        if report.status != ReportStatus.APPROVED:
            raise ConflictError(f"Report {report_id} must be approved before it can be published")
        published = await self._reports.publish(report_id, published_at=utcnow())
        if published is None:
            raise NotFoundError(f"Report {report_id} not found")
        return published


__all__ = ["ReportDraft", "ReportGenerator"]
