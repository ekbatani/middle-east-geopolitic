from typing import Literal

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

    llm_status = "not_configured" if not settings.llm_api_key else "ok"
    statuses.append(DependencyStatus(name="llm_provider", status=llm_status))

    return DependencyHealthResponse(dependencies=statuses)
