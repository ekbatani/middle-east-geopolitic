from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import APIRouter, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from apps.api.middleware.correlation import CorrelationIdMiddleware
from apps.api.routers import (
    actors,
    analyst_assessments,
    auth,
    claims,
    documents,
    events,
    forecasts,
    graph,
    health,
    imagery,
    indicators,
    intelligence,
    investigations,
    model_reviews,
    monitors,
    relationships,
    reports,
    review,
    risks,
    scenarios,
    schedules,
    sources,
)
from mei.application.services.scheduler import SchedulerService
from mei.shared.config import get_settings
from mei.shared.errors import MeiError
from mei.shared.logging import configure_logging

settings = get_settings()
configure_logging(json_output=settings.app_env != "development")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    scheduler = SchedulerService.get_instance()
    await scheduler.start()
    try:
        yield
    finally:
        await scheduler.stop()


def create_app() -> FastAPI:
    app = FastAPI(
        title="Middle East Geopolitical Intelligence Platform API",
        version="0.1.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.add_middleware(CorrelationIdMiddleware)

    @app.exception_handler(MeiError)
    async def mei_error_handler(request: Request, exc: MeiError) -> JSONResponse:
        # RFC 9457 problem-details response.
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "type": exc.problem_type,
                "title": exc.title,
                "status": exc.status_code,
                "detail": exc.detail,
                "instance": str(request.url.path),
            },
            media_type="application/problem+json",
        )

    app.include_router(health.router)
    # Minimal, build-step-free human-facing pages (geospatial map,
    # calibration dashboard) — design doc section 35, Phase 6.
    static_dir = Path(__file__).resolve().parent / "static"
    if static_dir.exists():
        app.mount("/static", StaticFiles(directory=static_dir), name="static")

    api_v1 = APIRouter(prefix="/api/v1")
    api_v1.include_router(auth.router)
    api_v1.include_router(actors.router)
    api_v1.include_router(sources.router)
    api_v1.include_router(documents.router)
    api_v1.include_router(claims.router)
    api_v1.include_router(events.router)
    api_v1.include_router(review.router)
    api_v1.include_router(relationships.router)
    api_v1.include_router(indicators.router)
    api_v1.include_router(risks.router)
    api_v1.include_router(scenarios.router)
    api_v1.include_router(forecasts.router)
    api_v1.include_router(reports.router)
    api_v1.include_router(intelligence.router)
    api_v1.include_router(investigations.router)
    api_v1.include_router(monitors.router)
    api_v1.include_router(graph.router)
    api_v1.include_router(analyst_assessments.router)
    api_v1.include_router(model_reviews.router)
    api_v1.include_router(imagery.router)
    api_v1.include_router(schedules.router)
    app.include_router(api_v1)

    return app


app = create_app()
