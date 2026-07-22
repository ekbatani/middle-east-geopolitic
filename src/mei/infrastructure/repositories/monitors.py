from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from mei.domain.monitors.models import Monitor, Notification


class MonitorRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, monitor_id: UUID) -> Monitor | None:
        return await self._session.get(Monitor, monitor_id)

    async def list_all(
        self,
        *,
        enabled: bool | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Monitor]:
        stmt = select(Monitor).order_by(Monitor.name.asc())
        if enabled is not None:
            stmt = stmt.where(Monitor.enabled == enabled)
        stmt = stmt.limit(limit).offset(offset)
        result = await self._session.execute(stmt)
        return list(result.scalars())

    async def create(
        self,
        *,
        name: str,
        user_id: UUID,
        monitor_type: str,
        condition_json: dict[str, object],
        schedule: str | None = None,
        delivery_channel: str = "telegram",
        enabled: bool = True,
    ) -> Monitor:
        monitor = Monitor(
            name=name,
            user_id=user_id,
            monitor_type=monitor_type,
            condition_json=condition_json,
            schedule=schedule,
            delivery_channel=delivery_channel,
            enabled=enabled,
        )
        self._session.add(monitor)
        await self._session.flush()
        return monitor

    async def delete(self, monitor_id: UUID) -> bool:
        monitor = await self.get(monitor_id)
        if monitor is None:
            return False
        await self._session.delete(monitor)
        await self._session.flush()
        return True

    async def create_notification(
        self,
        *,
        monitor_id: UUID | None,
        report_id: UUID | None,
        severity: str,
        title: str,
        body: str,
        delivery_channel: str,
    ) -> Notification:
        notification = Notification(
            monitor_id=monitor_id,
            report_id=report_id,
            severity=severity,
            title=title,
            body=body,
            delivery_channel=delivery_channel,
            status="pending",
        )
        self._session.add(notification)
        await self._session.flush()
        return notification

    async def get_notification(self, notification_id: UUID) -> Notification | None:
        return await self._session.get(Notification, notification_id)

    async def list_pending_notifications(self) -> list[Notification]:
        stmt = select(Notification).where(Notification.status == "pending")
        result = await self._session.execute(stmt)
        return list(result.scalars())


__all__ = ["MonitorRepository"]
