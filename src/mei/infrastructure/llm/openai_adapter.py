from typing import TypeVar

from openai import AsyncOpenAI
from pydantic import BaseModel

from mei.infrastructure.llm.prompts import load_prompt
from mei.shared.config import get_settings
from mei.shared.errors import LLMConfigurationError, LLMOutputError

T = TypeVar("T", bound=BaseModel)


class OpenAIStructuredLLM:
    """`StructuredLLM` backed by OpenAI's structured-output parsing.

    Never raises `LLMConfigurationError` at import time: the key is only
    required once a caller actually invokes an extraction task, so the rest
    of the app works fine without one configured.
    """

    def __init__(self, client: AsyncOpenAI | None = None, *, model: str | None = None) -> None:
        settings = get_settings()
        if client is None and not settings.llm_api_key:
            raise LLMConfigurationError("LLM_API_KEY is not configured")
        self._client = client or AsyncOpenAI(api_key=settings.llm_api_key)
        self._model = model or settings.llm_model

    async def generate_structured(
        self,
        *,
        task_name: str,
        prompt_version: str,
        input_text: str,
        output_model: type[T],
        metadata: dict[str, str],
    ) -> T:
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
        if parsed is None:
            raise LLMOutputError(
                f"{task_name}/{prompt_version} produced no valid structured output"
            )
        return parsed


__all__ = ["OpenAIStructuredLLM"]
