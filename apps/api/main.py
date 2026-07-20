from fastapi import APIRouter, FastAPI, Request
from fastapi.responses import JSONResponse
from prometheus_client import make_asgi_app

from apps.api.middleware.correlation import CorrelationIdMiddleware
from apps.api.routers import health
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
    # Domain routers (actors, sources, documents, claims, events, ...) are
    # registered here as they land, starting in Phase 1.
    app.include_router(api_v1)

    return app


app = create_app()
