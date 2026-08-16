from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from mei.domain.reports.models import Report
from mei.shared.enums import ReportStatus, ReportType, ScopeType


class ReportRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, report_id: UUID) -> Report | None:
        return await self._session.get(Report, report_id)

    async def list_all(
        self,
        *,
        report_type: ReportType | None = None,
        scope_type: ScopeType | None = None,
        scope_id: UUID | None = None,
        status: ReportStatus | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Report]:
        stmt = select(Report).order_by(Report.created_at.desc())
        if report_type is not None:
            stmt = stmt.where(Report.report_type == report_type)
        if scope_type is not None:
            stmt = stmt.where(Report.scope_type == scope_type)
        if scope_id is not None:
            stmt = stmt.where(Report.scope_id == scope_id)
        if status is not None:
            stmt = stmt.where(Report.status == status)
        stmt = stmt.limit(limit).offset(offset)
        result = await self._session.execute(stmt)
        return list(result.scalars())

    async def get_latest(
        self,
        *,
        report_type: ReportType,
        scope_type: ScopeType | None = None,
        scope_id: UUID | None = None,
    ) -> Report | None:
        stmt = select(Report).where(Report.report_type == report_type)
        if scope_type is not None:
            stmt = stmt.where(Report.scope_type == scope_type)
        if scope_id is not None:
            stmt = stmt.where(Report.scope_id == scope_id)
        stmt = stmt.order_by(Report.created_at.desc()).limit(1)
        result = await self._session.execute(stmt)
        return result.scalars().first()

    async def create(
        self,
        *,
        report_type: ReportType,
        title: str,
        scope_type: ScopeType | None,
        scope_id: UUID | None,
        period_start: date | None,
        period_end: date | None,
        content_markdown: str,
        content_object_key: str | None,
        generated_by_model: str | None,
        prompt_version: str | None,
    ) -> Report:
        report = Report(
            report_type=report_type,
            title=title,
            scope_type=scope_type,
            scope_id=scope_id,
            period_start=period_start,
            period_end=period_end,
            content_markdown=content_markdown,
            content_object_key=content_object_key,
            generated_by_model=generated_by_model,
            prompt_version=prompt_version,
        )
        self._session.add(report)
        await self._session.flush()
        return report

    async def approve(
        self, report_id: UUID, *, approved_by: str, approved_at: datetime
    ) -> Report | None:
        report = await self.get(report_id)
        if report is None:
            return None
        report.status = ReportStatus.APPROVED
        report.approved_by = approved_by
        report.approved_at = approved_at
        await self._session.flush()
        return report

    async def reject(self, report_id: UUID) -> Report | None:
        report = await self.get(report_id)
        if report is None:
            return None
        report.status = ReportStatus.REJECTED
        await self._session.flush()
        return report

    async def publish(self, report_id: UUID, *, published_at: datetime) -> Report | None:
        report = await self.get(report_id)
        if report is None:
            return None
        report.status = ReportStatus.PUBLISHED
        report.published_at = published_at
        await self._session.flush()
        return report

    async def update(
        self,
        report: Report,
        *,
        title: str | None = None,
        content_markdown: str | None = None,
        status: ReportStatus | None = None,
    ) -> Report:
        if title is not None:
            report.title = title
        if content_markdown is not None:
            report.content_markdown = content_markdown
        if status is not None:
            report.status = status
        await self._session.flush()
        return report

    async def delete(self, report: Report) -> None:
        await self._session.delete(report)
        await self._session.flush()


__all__ = ["ReportRepository"]

