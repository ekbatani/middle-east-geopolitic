from typing import Protocol, TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class StructuredLLM(Protocol):
    """Provider-agnostic structured-output interface (design doc section 13.1).

    Every extraction/analytical operation goes through this rather than a
    provider SDK directly, so adapters (OpenAI-compatible, local models,
    the deterministic test fake) are interchangeable and every call site
    gets validated Pydantic output instead of raw text.
    """

    async def generate_structured(
        self,
        *,
        task_name: str,
        prompt_version: str,
        input_text: str,
        output_model: type[T],
        metadata: dict[str, str],
    ) -> T: ...


__all__ = ["StructuredLLM", "T"]
