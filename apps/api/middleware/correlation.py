import time
import uuid
from collections.abc import Awaitable, Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from mei.shared.logging import get_logger, set_correlation_id

logger = get_logger(__name__)

CORRELATION_ID_HEADER = "X-Request-ID"


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    """Assigns (or propagates) a request correlation ID and logs each request.

    The same ID should be threaded through Celery tasks and LLM calls
    triggered by this request so one investigation can be traced end to
    end in the logs.
    """

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        correlation_id = request.headers.get(CORRELATION_ID_HEADER, str(uuid.uuid4()))
        set_correlation_id(correlation_id)

        started_at = time.perf_counter()
        logger.info("request.started", method=request.method, path=request.url.path)

        response = await call_next(request)

        duration_ms = round((time.perf_counter() - started_at) * 1000, 2)
        response.headers[CORRELATION_ID_HEADER] = correlation_id
        logger.info(
            "request.completed",
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration_ms=duration_ms,
        )
        return response
