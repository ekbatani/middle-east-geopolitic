from sqlalchemy.ext.asyncio import AsyncSession

from mei.domain.audit.models import AuditLog
from mei.shared.enums import AuditActorType


class AuditRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def record(
        self,
        *,
        actor_type: AuditActorType,
        actor_id: str | None,
        action: str,
        resource_type: str | None = None,
        resource_id: str | None = None,
        correlation_id: str | None = None,
        metadata: dict[str, object] | None = None,
    ) -> AuditLog:
        entry = AuditLog(
            actor_type=actor_type,
            actor_id=actor_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            correlation_id=correlation_id,
            metadata_json=metadata or {},
        )
        self._session.add(entry)
        await self._session.flush()
        return entry


__all__ = ["AuditRepository"]
