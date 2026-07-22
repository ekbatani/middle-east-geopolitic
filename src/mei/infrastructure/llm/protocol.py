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
        """Vision-input counterpart to `generate_structured` (design doc
        section 35, Phase 6 "imagery evidence"). A separate method rather
        than an optional parameter: the two call shapes are genuinely
        different at the provider-SDK level (a multimodal content list vs.
        a plain string), and every existing call site keeps using
        `generate_structured` untouched."""
        ...


__all__ = ["StructuredLLM", "T"]
