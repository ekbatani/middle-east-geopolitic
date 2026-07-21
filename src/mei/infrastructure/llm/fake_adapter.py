from collections.abc import Callable
from typing import TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)

FakeResponse = BaseModel | Callable[[str], BaseModel]


class FakeStructuredLLM:
    """Deterministic `StructuredLLM` stand-in used by every test.

    `responses` maps `task_name` to either a fixed model instance or a
    `(input_text) -> BaseModel` callable for input-dependent fixtures. Never
    falls back to a fabricated default: an unregistered task raises, so a
    test forgetting to stub a call fails loudly instead of silently
    exercising an empty extraction result.
    """

    def __init__(self, responses: dict[str, FakeResponse]) -> None:
        self._responses = responses

    async def generate_structured(
        self,
        *,
        task_name: str,
        prompt_version: str,
        input_text: str,
        output_model: type[T],
        metadata: dict[str, str],
    ) -> T:
        try:
            response = self._responses[task_name]
        except KeyError as exc:
            raise KeyError(
                f"FakeStructuredLLM has no response registered for task '{task_name}'"
            ) from exc

        result = response(input_text) if callable(response) else response
        if not isinstance(result, output_model):
            raise TypeError(
                f"Fake response for '{task_name}' is a {type(result).__name__}, "
                f"expected {output_model.__name__}"
            )
        return result


__all__ = ["FakeStructuredLLM"]
