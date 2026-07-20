from typing import Literal

import redis.asyncio as redis
from fastapi import APIRouter
from pydantic import BaseModel
from sqlalchemy import text

from apps.api.dependencies import SessionDep, SettingsDep

router = APIRouter(prefix="/health", tags=["health"])


class LivenessResponse(BaseModel):
    status: Literal["ok"] = "ok"


class ReadinessResponse(BaseModel):
    status: Literal["ok", "unavailable"]
    database: Literal["ok", "unavailable"]


class DependencyStatus(BaseModel):
    name: str
    status: Literal["ok", "unavailable", "not_configured"]


class DependencyHealthResponse(BaseModel):
    dependencies: list[DependencyStatus]


@router.get("/live", response_model=LivenessResponse)
async def liveness() -> LivenessResponse:
    return LivenessResponse()


@router.get("/ready", response_model=ReadinessResponse)
async def readiness(session: SessionDep) -> ReadinessResponse:
    try:
        await session.execute(text("SELECT 1"))
        database_status: Literal["ok", "unavailable"] = "ok"
    except Exception:
        database_status = "unavailable"

    overall = "ok" if database_status == "ok" else "unavailable"
    return ReadinessResponse(status=overall, database=database_status)


@router.get("/dependencies", response_model=DependencyHealthResponse)
async def dependency_health(settings: SettingsDep) -> DependencyHealthResponse:
    statuses: list[DependencyStatus] = []

    try:
        client = redis.from_url(  # type: ignore[no-untyped-call]
            settings.redis_url, socket_connect_timeout=2
        )
        await client.ping()
        await client.aclose()
        statuses.append(DependencyStatus(name="redis", status="ok"))
    except Exception:
        statuses.append(DependencyStatus(name="redis", status="unavailable"))

    object_storage_status = "not_configured" if not settings.s3_bucket else "ok"
    statuses.append(DependencyStatus(name="object_storage", status=object_storage_status))

    llm_status = "not_configured" if not settings.llm_api_key else "ok"
    statuses.append(DependencyStatus(name="llm_provider", status=llm_status))

    return DependencyHealthResponse(dependencies=statuses)
