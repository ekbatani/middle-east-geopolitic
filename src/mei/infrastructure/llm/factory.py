from mei.infrastructure.llm.openai_adapter import OpenAIStructuredLLM
from mei.infrastructure.llm.protocol import StructuredLLM
from mei.shared.config import get_settings


def get_structured_llm() -> StructuredLLM:
    """Select the configured `StructuredLLM` adapter (section 13.1).

    Tests inject `FakeStructuredLLM` directly rather than going through this
    factory, so it only ever needs to resolve real providers.
    """
    settings = get_settings()
    if settings.llm_provider == "openai":
        return OpenAIStructuredLLM()
    raise ValueError(f"Unsupported LLM provider: {settings.llm_provider}")


__all__ = ["get_structured_llm"]
