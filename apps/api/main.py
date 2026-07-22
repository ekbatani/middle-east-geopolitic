from fastapi import APIRouter, FastAPI, Request
from fastapi.responses import JSONResponse
from prometheus_client import make_asgi_app

from apps.api.middleware.correlation import CorrelationIdMiddleware
from apps.api.routers import (
    actors,
    auth,
    claims,
    documents,
    events,
    forecasts,
    graph,
    health,
    indicators,
    intelligence,
    investigations,
    monitors,
    relationships,
    reports,
    review,
    risks,
    scenarios,
    sources,
)
from mei.shared.config import get_settings
from mei.shared.errors import MeiError
from mei.shared.logging import configure_logging

settings = get_settings()
configure_logging(json_output=settings.app_env != "development")


def create_app() -> FastAPI:
    app = FastAPI(
        title="Middle East Geopolitical Intelligence Platform API",
        version="0.1.0",
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
    app.mount("/metrics", make_asgi_app())

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
    app.include_router(api_v1)

    return app


app = create_app()
