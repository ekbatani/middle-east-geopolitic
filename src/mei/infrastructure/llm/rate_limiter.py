from __future__ import annotations

import asyncio
import random
import time
from collections.abc import Awaitable, Callable
from typing import TypeVar

import openai

from mei.shared.logging import get_logger

logger = get_logger(__name__)

T = TypeVar("T")

# Shared registry to ensure multiple adapter instances sharing a provider endpoint
# share the same concurrency semaphore and rate-limiting queue.
_LIMITER_REGISTRY: dict[str, AsyncRateLimiter] = {}


class AsyncRateLimiter:
    """Queues and throttles LLM requests, enforcing concurrency limits,
    minimum inter-request intervals, and exponential backoff retries on 429
    (RateLimitError) and transient upstream failures.
    """

    def __init__(
        self,
        *,
        max_concurrency: int = 1,
        min_interval_seconds: float = 0.0,
        max_retries: int = 5,
        backoff_base_seconds: float = 2.0,
        backoff_max_seconds: float = 60.0,
    ) -> None:
        self.max_concurrency = max(1, max_concurrency)
        self.min_interval_seconds = max(0.0, min_interval_seconds)
        self.max_retries = max(0, max_retries)
        self.backoff_base_seconds = max(0.1, backoff_base_seconds)
        self.backoff_max_seconds = max(1.0, backoff_max_seconds)

        self._semaphore = asyncio.Semaphore(self.max_concurrency)
        self._pacing_lock = asyncio.Lock()
        self._last_request_time: float = 0.0

    async def _pace(self) -> None:
        """Ensure requests are spaced by at least `min_interval_seconds`."""
        if self.min_interval_seconds <= 0.0:
            return

        async with self._pacing_lock:
            now = time.monotonic()
            elapsed = now - self._last_request_time
            if elapsed < self.min_interval_seconds:
                delay = self.min_interval_seconds - elapsed
                await asyncio.sleep(delay)
            self._last_request_time = time.monotonic()

    def _extract_retry_after(self, exc: Exception) -> float | None:
        """Check for standard Retry-After header or delay hints on error."""
        if isinstance(exc, openai.APIStatusError) and exc.response is not None:
            retry_header = exc.response.headers.get("retry-after")
            if retry_header:
                try:
                    return float(retry_header)
                except ValueError:
                    pass
        return None

    def _is_retryable(self, exc: Exception) -> bool:
        """Determine if an exception represents a rate limit or transient network/server failure."""
        if isinstance(exc, (openai.RateLimitError, openai.APIConnectionError, openai.InternalServerError)):
            return True
        return bool(
            isinstance(exc, openai.APIStatusError)
            and exc.status_code in (429, 500, 502, 503, 504, 529)
        )

    async def execute(self, func: Callable[[], Awaitable[T]], *, task_name: str = "llm_request") -> T:
        """Execute the async function inside the concurrency queue, paced, with backoff retries."""
        attempt = 0
        while True:
            async with self._semaphore:
                await self._pace()
                try:
                    return await func()
                except Exception as exc:
                    if not self._is_retryable(exc) or attempt >= self.max_retries:
                        if attempt >= self.max_retries:
                            logger.error(
                                "llm.rate_limiter.retries_exhausted",
                                task=task_name,
                                attempts=attempt + 1,
                                error=str(exc),
                            )
                        raise

                    attempt += 1

                    # Determine backoff duration
                    retry_after = self._extract_retry_after(exc)
                    if retry_after is not None:
                        delay = min(self.backoff_max_seconds, retry_after)
                    else:
                        base = self.backoff_base_seconds * (2 ** (attempt - 1))
                        jitter = random.uniform(0.1, 0.6)
                        delay = min(self.backoff_max_seconds, base + jitter)

                    logger.warning(
                        "llm.rate_limiter.throttled_retry",
                        task=task_name,
                        attempt=attempt,
                        max_retries=self.max_retries,
                        backoff_seconds=round(delay, 2),
                        error=str(exc),
                    )

            # Wait outside semaphore so other queue slots can make progress if allowed
            await asyncio.sleep(delay)


def get_shared_rate_limiter(
    key: str,
    *,
    max_concurrency: int = 1,
    min_interval_seconds: float = 0.0,
    max_retries: int = 5,
    backoff_base_seconds: float = 2.0,
    backoff_max_seconds: float = 60.0,
) -> AsyncRateLimiter:
    """Retrieve or create a singleton rate limiter instance for a specific provider/endpoint."""
    if key not in _LIMITER_REGISTRY:
        _LIMITER_REGISTRY[key] = AsyncRateLimiter(
            max_concurrency=max_concurrency,
            min_interval_seconds=min_interval_seconds,
            max_retries=max_retries,
            backoff_base_seconds=backoff_base_seconds,
            backoff_max_seconds=backoff_max_seconds,
        )
    return _LIMITER_REGISTRY[key]


def reset_rate_limiters() -> None:
    """Clear all registered rate limiters (useful for testing)."""
    _LIMITER_REGISTRY.clear()


__all__ = ["AsyncRateLimiter", "get_shared_rate_limiter", "reset_rate_limiters"]
