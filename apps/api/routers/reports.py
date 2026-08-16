from datetime import date, datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from apps.api.audit import audit
from apps.api.dependencies import SessionDep, require_scopes
from mei.application.services.report_generator import ReportGenerator
from mei.domain.reports.models import Report
from mei.infrastructure.auth.principal import Principal
from mei.infrastructure.llm.factory import get_structured_llm
from mei.infrastructure.llm.protocol import StructuredLLM
from mei.infrastructure.repositories.reports import ReportRepository
from mei.shared.enums import ReportStatus, ReportType, Scope, ScopeType
from mei.shared.errors import LLMConfigurationError, NotFoundError

router = APIRouter(prefix="/reports", tags=["reports"])

ReadPrincipal = Annotated[Principal, Depends(require_scopes(Scope.INTELLIGENCE_READ))]
GeneratePrincipal = Annotated[Principal, Depends(require_scopes(Scope.REPORTS_GENERATE))]
ApprovePrincipal = Annotated[Principal, Depends(require_scopes(Scope.REPORTS_APPROVE))]


def _try_get_llm() -> StructuredLLM | None:
    """Best-effort narrative drafting: report generation must still succeed
    — with a plain deterministic executive-assessment placeholder — when
    no provider is configured, matching the risk/scenario engines."""
    try:
        return get_structured_llm()
    except LLMConfigurationError:
        return None


class ReportOut(BaseModel):
    id: UUID
    report_type: ReportType
    title: str
    scope_type: ScopeType | None
    scope_id: UUID | None
    period_start: date | None
    period_end: date | None
    content_markdown: str
    content_object_key: str | None
    status: ReportStatus
    generated_by_model: str | None
    prompt_version: str | None
    approved_by: str | None
    approved_at: datetime | None
    published_at: datetime | None

    @classmethod
    def from_domain(cls, report: Report) -> "ReportOut":
        return cls(
            id=report.id,
            report_type=report.report_type,
            title=report.title,
            scope_type=report.scope_type,
            scope_id=report.scope_id,
            period_start=report.period_start,
            period_end=report.period_end,
            content_markdown=report.content_markdown,
            content_object_key=report.content_object_key,
            status=report.status,
            generated_by_model=report.generated_by_model,
            prompt_version=report.prompt_version,
            approved_by=report.approved_by,
            approved_at=report.approved_at,
            published_at=report.published_at,
        )


class ReportSummaryOut(BaseModel):
    """List view omits `content_markdown` — full bodies are fetched per-report."""

    id: UUID
    report_type: ReportType
    title: str
    scope_type: ScopeType | None
    scope_id: UUID | None
    period_start: date | None
    period_end: date | None
    status: ReportStatus
    published_at: datetime | None

    @classmethod
    def from_domain(cls, report: Report) -> "ReportSummaryOut":
        return cls(
            id=report.id,
            report_type=report.report_type,
            title=report.title,
            scope_type=report.scope_type,
            scope_id=report.scope_id,
            period_start=report.period_start,
            period_end=report.period_end,
            status=report.status,
            published_at=report.published_at,
        )


class GenerateReportRequest(BaseModel):
    report_type: ReportType
    scope_type: ScopeType | None = None
    scope_id: UUID | None = None


@router.get("", response_model=list[ReportSummaryOut])
async def list_reports(
    session: SessionDep,
    _principal: ReadPrincipal,
    report_type: ReportType | None = None,
    scope_type: ScopeType | None = None,
    scope_id: UUID | None = None,
    status: ReportStatus | None = None,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> list[ReportSummaryOut]:
    reports = await ReportRepository(session).list_all(
        report_type=report_type,
        scope_type=scope_type,
        scope_id=scope_id,
        status=status,
        limit=limit,
        offset=offset,
    )
    return [ReportSummaryOut.from_domain(r) for r in reports]


@router.get("/{report_id}", response_model=ReportOut)
async def get_report(report_id: UUID, session: SessionDep, _principal: ReadPrincipal) -> ReportOut:
    report = await ReportRepository(session).get(report_id)
    if report is None:
        raise NotFoundError(f"Report {report_id} not found")
    return ReportOut.from_domain(report)


@router.post("/generate", response_model=ReportOut, status_code=201)
async def generate_report(
    payload: GenerateReportRequest, session: SessionDep, principal: GeneratePrincipal
) -> ReportOut:
    report = await ReportGenerator(session).generate(
        payload.report_type,
        scope_type=payload.scope_type,
        scope_id=payload.scope_id,
        llm=_try_get_llm(),
        triggered_by=str(principal.user_id),
    )
    await audit(
        session,
        principal,
        "report.generated",
        resource_type="report",
        resource_id=str(report.id),
        metadata={"report_type": str(payload.report_type)},
    )
    return ReportOut.from_domain(report)


@router.post("/{report_id}/approve", response_model=ReportOut)
async def approve_report(
    report_id: UUID, session: SessionDep, principal: ApprovePrincipal
) -> ReportOut:
    report = await ReportGenerator(session).approve_report(
        report_id, approved_by=str(principal.user_id)
    )
    await audit(
        session, principal, "report.approved", resource_type="report", resource_id=str(report_id)
    )
    return ReportOut.from_domain(report)


@router.post("/{report_id}/reject", response_model=ReportOut)
async def reject_report(
    report_id: UUID, session: SessionDep, principal: ApprovePrincipal
) -> ReportOut:
    report = await ReportGenerator(session).reject_report(report_id)
    await audit(
        session, principal, "report.rejected", resource_type="report", resource_id=str(report_id)
    )
    return ReportOut.from_domain(report)


@router.post("/{report_id}/publish", response_model=ReportOut)
async def publish_report(
    report_id: UUID, session: SessionDep, principal: ApprovePrincipal
) -> ReportOut:
    report = await ReportGenerator(session).publish_report(report_id)
    await audit(
        session, principal, "report.published", resource_type="report", resource_id=str(report_id)
    )
    return ReportOut.from_domain(report)


class UpdateReportRequest(BaseModel):
    title: str | None = None
    content_markdown: str | None = None
    status: ReportStatus | None = None


@router.patch("/{report_id}", response_model=ReportOut)
async def update_report(
    report_id: UUID,
    payload: UpdateReportRequest,
    session: SessionDep,
    principal: ApprovePrincipal,
) -> ReportOut:
    repo = ReportRepository(session)
    report = await repo.get(report_id)
    if report is None:
        raise NotFoundError(f"Report {report_id} not found")

    updated = await repo.update(
        report,
        title=payload.title,
        content_markdown=payload.content_markdown,
        status=payload.status,
    )
    await audit(
        session,
        principal,
        "report.updated",
        resource_type="report",
        resource_id=str(report_id),
        metadata=payload.model_dump(exclude_unset=True),
    )
    await session.commit()
    return ReportOut.from_domain(updated)


@router.delete("/{report_id}", status_code=204)
async def delete_report(
    report_id: UUID,
    session: SessionDep,
    principal: ApprovePrincipal,
) -> None:
    repo = ReportRepository(session)
    report = await repo.get(report_id)
    if report is None:
        raise NotFoundError(f"Report {report_id} not found")

    await repo.delete(report)
    await audit(
        session,
        principal,
        "report.deleted",
        resource_type="report",
        resource_id=str(report_id),
    )
    await session.commit()

