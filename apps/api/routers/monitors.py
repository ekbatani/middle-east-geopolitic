from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, ConfigDict, Field

from apps.api.audit import audit
from apps.api.dependencies import SessionDep, require_scopes
from mei.infrastructure.auth.principal import Principal
from mei.infrastructure.repositories.monitors import MonitorRepository
from mei.shared.enums import Scope
from mei.shared.errors import NotFoundError

router = APIRouter(prefix="/monitors", tags=["monitors"])

ManagePrincipal = Annotated[Principal, Depends(require_scopes(Scope.MONITORS_MANAGE))]


class MonitorOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    user_id: UUID
    monitor_type: str
    condition_json: dict[str, object]
    schedule: str | None
    delivery_channel: str
    enabled: bool
    last_evaluated_at: datetime | None
    last_triggered_at: datetime | None


class CreateMonitorRequest(BaseModel):
    name: str = Field(min_length=1, max_length=300)
    monitor_type: str = Field(min_length=1)  # relationship_threshold, country_risk
    condition_json: dict[str, object]
    schedule: str | None = None
    delivery_channel: str = "telegram"
    enabled: bool = True


class UpdateMonitorRequest(BaseModel):
    name: str | None = None
    condition_json: dict[str, object] | None = None
    schedule: str | None = None
    delivery_channel: str | None = None
    enabled: bool | None = None


@router.post("", response_model=MonitorOut, status_code=201)
async def create_monitor(
    payload: CreateMonitorRequest,
    session: SessionDep,
    principal: ManagePrincipal,
) -> MonitorOut:
    repo = MonitorRepository(session)
    monitor = await repo.create(
        name=payload.name,
        user_id=principal.user_id,
        monitor_type=payload.monitor_type,
        condition_json=payload.condition_json,
        schedule=payload.schedule,
        delivery_channel=payload.delivery_channel,
        enabled=payload.enabled,
    )
    await audit(
        session,
        principal,
        "monitor.created",
        resource_type="monitor",
        resource_id=str(monitor.id),
        metadata={"monitor_type": payload.monitor_type},
    )
    return MonitorOut.model_validate(monitor)


@router.patch("/{monitor_id}", response_model=MonitorOut)
async def update_monitor(
    monitor_id: UUID,
    payload: UpdateMonitorRequest,
    session: SessionDep,
    principal: ManagePrincipal,
) -> MonitorOut:
    repo = MonitorRepository(session)
    monitor = await repo.get(monitor_id)
    if not monitor:
        raise NotFoundError(f"Monitor {monitor_id} not found")

    if payload.name is not None:
        monitor.name = payload.name
    if payload.condition_json is not None:
        monitor.condition_json = payload.condition_json
    if payload.schedule is not None:
        monitor.schedule = payload.schedule
    if payload.delivery_channel is not None:
        monitor.delivery_channel = payload.delivery_channel
    if payload.enabled is not None:
        monitor.enabled = payload.enabled

    await session.flush()
    await audit(
        session,
        principal,
        "monitor.updated",
        resource_type="monitor",
        resource_id=str(monitor.id),
    )
    return MonitorOut.model_validate(monitor)


@router.delete("/{monitor_id}", status_code=204)
async def delete_monitor(
    monitor_id: UUID,
    session: SessionDep,
    principal: ManagePrincipal,
) -> None:
    repo = MonitorRepository(session)
    deleted = await repo.delete(monitor_id)
    if not deleted:
        raise NotFoundError(f"Monitor {monitor_id} not found")
    await audit(
        session,
        principal,
        "monitor.deleted",
        resource_type="monitor",
        resource_id=str(monitor_id),
    )


@router.get("", response_model=list[MonitorOut])
async def list_monitors(
    session: SessionDep,
    _principal: ManagePrincipal,
    enabled: bool | None = None,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> list[MonitorOut]:
    repo = MonitorRepository(session)
    monitors = await repo.list_all(
        enabled=enabled,
        limit=limit,
        offset=offset,
    )
    return [MonitorOut.model_validate(m) for m in monitors]


@router.get("/{monitor_id}", response_model=MonitorOut)
async def get_monitor(
    monitor_id: UUID,
    session: SessionDep,
    _principal: ManagePrincipal,
) -> MonitorOut:
    repo = MonitorRepository(session)
    monitor = await repo.get(monitor_id)
    if not monitor:
        raise NotFoundError(f"Monitor {monitor_id} not found")
    return MonitorOut.model_validate(monitor)


__all__ = ["router"]
