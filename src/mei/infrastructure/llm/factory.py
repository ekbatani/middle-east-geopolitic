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


def get_secondary_structured_llm() -> StructuredLLM | None:
    """The second model multi-model review shadow-runs high-impact risk
    assessments against (design doc section 35, Phase 6). `None` when
    `LLM_SECONDARY_MODEL` isn't configured — the feature is opt-in, not a
    hard requirement to run the platform."""
    settings = get_settings()
    if not settings.llm_secondary_model:
        return None
    if settings.llm_provider == "openai":
        return OpenAIStructuredLLM(model=settings.llm_secondary_model)
    raise ValueError(f"Unsupported LLM provider: {settings.llm_provider}")


__all__ = ["get_secondary_structured_llm", "get_structured_llm"]
