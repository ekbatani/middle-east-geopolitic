import asyncio
import time

import httpx
import openai
import pytest

from mei.infrastructure.llm.rate_limiter import (
    AsyncRateLimiter,
    get_shared_rate_limiter,
    reset_rate_limiters,
)


def _make_rate_limit_error(status_code: int = 429, retry_after: str | None = None) -> openai.RateLimitError:
    headers = {"retry-after": retry_after} if retry_after else {}
    response = httpx.Response(
        status_code=status_code,
        headers=headers,
        request=httpx.Request("POST", "https://api.openai.com/v1/chat/completions"),
    )
    return openai.RateLimitError(
        message="Rate limit exceeded",
        response=response,
        body={"error": {"message": "Rate limit exceeded"}},
    )


async def test_concurrency_is_strictly_enforced() -> None:
    limiter = AsyncRateLimiter(max_concurrency=1, min_interval_seconds=0.0)
    current_concurrent = 0
    max_observed_concurrent = 0

    async def worker() -> str:
        nonlocal current_concurrent, max_observed_concurrent
        current_concurrent += 1
        max_observed_concurrent = max(max_observed_concurrent, current_concurrent)
        await asyncio.sleep(0.05)
        current_concurrent -= 1
        return "ok"

    results = await asyncio.gather(
        limiter.execute(worker),
        limiter.execute(worker),
        limiter.execute(worker),
    )

    assert results == ["ok", "ok", "ok"]
    assert max_observed_concurrent == 1


async def test_request_pacing_spaces_requests() -> None:
    limiter = AsyncRateLimiter(max_concurrency=2, min_interval_seconds=0.08)

    async def quick_worker() -> str:
        return "done"

    start = time.perf_counter()
    results = await asyncio.gather(
        limiter.execute(quick_worker),
        limiter.execute(quick_worker),
        limiter.execute(quick_worker),
    )
    elapsed = time.perf_counter() - start

    assert results == ["done", "done", "done"]
    # 3 requests with 0.08s interval should take at least ~0.15s
    assert elapsed >= 0.14


async def test_retries_on_rate_limit_and_succeeds() -> None:
    limiter = AsyncRateLimiter(
        max_concurrency=1,
        min_interval_seconds=0.0,
        max_retries=3,
        backoff_base_seconds=0.01,
        backoff_max_seconds=0.1,
    )
    call_count = 0

    async def flaky_worker() -> str:
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise _make_rate_limit_error()
        return "recovered"

    result = await limiter.execute(flaky_worker)
    assert result == "recovered"
    assert call_count == 3


async def test_retries_exhausted_raises_error() -> None:
    limiter = AsyncRateLimiter(
        max_concurrency=1,
        min_interval_seconds=0.0,
        max_retries=2,
        backoff_base_seconds=0.01,
        backoff_max_seconds=0.05,
    )
    call_count = 0

    async def failing_worker() -> str:
        nonlocal call_count
        call_count += 1
        raise _make_rate_limit_error()

    with pytest.raises(openai.RateLimitError):
        await limiter.execute(failing_worker)

    assert call_count == 3  # Initial + 2 retries


async def test_non_retryable_error_fails_immediately() -> None:
    limiter = AsyncRateLimiter(max_concurrency=1, max_retries=5)
    call_count = 0

    async def invalid_worker() -> str:
        nonlocal call_count
        call_count += 1
        raise ValueError("Invalid schema")

    with pytest.raises(ValueError, match="Invalid schema"):
        await limiter.execute(invalid_worker)

    assert call_count == 1


async def test_shared_limiter_registry() -> None:
    reset_rate_limiters()
    limiter1 = get_shared_rate_limiter("endpoint_a", max_concurrency=2)
    limiter2 = get_shared_rate_limiter("endpoint_a", max_concurrency=2)
    limiter3 = get_shared_rate_limiter("endpoint_b", max_concurrency=1)

    assert limiter1 is limiter2
    assert limiter1 is not limiter3
