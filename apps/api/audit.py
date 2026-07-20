from sqlalchemy.ext.asyncio import AsyncSession

from mei.infrastructure.auth.principal import Principal
from mei.infrastructure.repositories.audit import AuditRepository
from mei.shared.enums import AuditActorType
from mei.shared.logging import get_correlation_id


async def audit(
    session: AsyncSession,
    principal: Principal,
    action: str,
    *,
    resource_type: str | None = None,
    resource_id: str | None = None,
    metadata: dict[str, object] | None = None,
) -> None:
    actor_type = AuditActorType.API_KEY if principal.api_key_id else AuditActorType.USER
    await AuditRepository(session).record(
        actor_type=actor_type,
        actor_id=str(principal.user_id),
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        correlation_id=get_correlation_id(),
        metadata=metadata,
    )


__all__ = ["audit"]
