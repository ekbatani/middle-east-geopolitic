import base64
import contextlib
from typing import Any, TypeVar

from openai import AsyncOpenAI
from pydantic import BaseModel

from mei.infrastructure.llm.prompts import load_prompt
from mei.infrastructure.llm.rate_limiter import AsyncRateLimiter, get_shared_rate_limiter
from mei.shared.config import get_settings
from mei.shared.errors import LLMConfigurationError, LLMOutputError

T = TypeVar("T", bound=BaseModel)


class OpenAIStructuredLLM:
    """`StructuredLLM` backed by OpenAI's structured-output parsing with
    built-in concurrency throttling, request pacing, and backoff retry.

    Never raises `LLMConfigurationError` at import time: the key is only
    required once a caller actually invokes an extraction task, so the rest
    of the app works fine without one configured.
    """

    def __init__(
        self,
        client: AsyncOpenAI | None = None,
        *,
        model: str | None = None,
        base_url: str | None = None,
        api_key: str | None = None,
        default_headers: dict[str, str] | None = None,
        rate_limiter: AsyncRateLimiter | None = None,
        max_concurrency: int | None = None,
        min_interval_seconds: float | None = None,
        max_retries: int | None = None,
        backoff_base_seconds: float | None = None,
        backoff_max_seconds: float | None = None,
    ) -> None:
        settings = get_settings()
        resolved_key = api_key or settings.llm_api_key
        if client is None and not resolved_key:
            raise LLMConfigurationError("LLM_API_KEY is not configured")
        resolved_base_url = base_url or settings.llm_base_url or None
        if client is None:
            client_kwargs: dict[str, Any] = {"api_key": resolved_key}
            if resolved_base_url:
                client_kwargs["base_url"] = resolved_base_url
            if default_headers:
                client_kwargs["default_headers"] = default_headers
            self._client = AsyncOpenAI(**client_kwargs)
        else:
            self._client = client
        self._model = model or settings.llm_model

        if rate_limiter is not None:
            self._rate_limiter = rate_limiter
        else:
            resolved_concurrency = (
                max_concurrency if max_concurrency is not None else (settings.llm_max_concurrency or 1)
            )
            resolved_interval = (
                min_interval_seconds
                if min_interval_seconds is not None
                else (settings.llm_min_request_interval_seconds if settings.llm_min_request_interval_seconds >= 0 else 0.0)
            )
            resolved_retries = max_retries if max_retries is not None else settings.llm_max_retries
            resolved_backoff_base = (
                backoff_base_seconds
                if backoff_base_seconds is not None
                else settings.llm_retry_backoff_base_seconds
            )
            resolved_backoff_max = (
                backoff_max_seconds
                if backoff_max_seconds is not None
                else settings.llm_retry_backoff_max_seconds
            )

            limiter_key = f"{resolved_base_url or 'https://api.openai.com/v1'}:{self._model}"
            self._rate_limiter = get_shared_rate_limiter(
                limiter_key,
                max_concurrency=resolved_concurrency,
                min_interval_seconds=resolved_interval,
                max_retries=resolved_retries,
                backoff_base_seconds=resolved_backoff_base,
                backoff_max_seconds=resolved_backoff_max,
            )

    async def generate_structured(
        self,
        *,
        task_name: str,
        prompt_version: str,
        input_text: str,
        output_model: type[T],
        metadata: dict[str, str],
    ) -> T:
        async def _call() -> T:
            system_prompt = load_prompt(task_name, prompt_version)
            completion = await self._client.beta.chat.completions.parse(
                model=self._model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": input_text},
                ],
                response_format=output_model,
            )
            parsed = completion.choices[0].message.parsed
            if parsed is None and completion.choices[0].message.content:
                with contextlib.suppress(Exception):
                    parsed = output_model.model_validate_json(completion.choices[0].message.content)
            if parsed is None:
                raise LLMOutputError(
                    f"{task_name}/{prompt_version} produced no valid structured output"
                )
            return parsed

        return await self._rate_limiter.execute(_call, task_name=f"{task_name}/{prompt_version}")

    async def generate_structured_from_image(
        self,
        *,
        task_name: str,
        prompt_version: str,
        image_bytes: bytes,
        content_type: str,
        output_model: type[T],
        metadata: dict[str, str],
    ) -> T:
        async def _call() -> T:
            system_prompt = load_prompt(task_name, prompt_version)
            encoded = base64.b64encode(image_bytes).decode("ascii")
            completion = await self._client.beta.chat.completions.parse(
                model=self._model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image_url",
                                "image_url": {"url": f"data:{content_type};base64,{encoded}"},
                            }
                        ],
                    },
                ],
                response_format=output_model,
            )
            parsed = completion.choices[0].message.parsed
            if parsed is None and completion.choices[0].message.content:
                with contextlib.suppress(Exception):
                    parsed = output_model.model_validate_json(completion.choices[0].message.content)
            if parsed is None:
                raise LLMOutputError(
                    f"{task_name}/{prompt_version} produced no valid structured output"
                )
            return parsed

        return await self._rate_limiter.execute(_call, task_name=f"{task_name}/{prompt_version}")


__all__ = ["OpenAIStructuredLLM"]
