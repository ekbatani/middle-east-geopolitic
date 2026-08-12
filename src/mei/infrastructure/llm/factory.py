from mei.infrastructure.llm.openai_adapter import OpenAIStructuredLLM
from mei.infrastructure.llm.protocol import StructuredLLM
from mei.shared.config import get_settings

PROVIDER_BASE_URLS: dict[str, str] = {
    "openrouter": "https://openrouter.ai/api/v1",
    "opencode_go": "https://api.opencode.ai/v1",
    "opencode": "https://api.opencode.ai/v1",
    "opencode-go": "https://api.opencode.ai/v1",
    "nvidia_build": "https://integrate.api.nvidia.com/v1",
    "nvidia": "https://integrate.api.nvidia.com/v1",
    "nvidia-build": "https://integrate.api.nvidia.com/v1",
    "ollama": "http://localhost:11434/v1",
}


def _create_llm_adapter(provider: str, model: str | None = None) -> StructuredLLM:
    settings = get_settings()
    provider_key = provider.lower().strip()
    if provider_key != "openai" and provider_key not in PROVIDER_BASE_URLS:
        raise ValueError(f"Unsupported LLM provider: {settings.llm_provider}")

    base_url = settings.llm_base_url or PROVIDER_BASE_URLS.get(provider_key)
    return OpenAIStructuredLLM(model=model, base_url=base_url)


def get_structured_llm() -> StructuredLLM:
    """Select the configured `StructuredLLM` adapter (section 13.1).

    Tests inject `FakeStructuredLLM` directly rather than going through this
    factory, so it only ever needs to resolve real providers.
    """
    settings = get_settings()
    return _create_llm_adapter(settings.llm_provider)


def get_secondary_structured_llm() -> StructuredLLM | None:
    """The second model multi-model review shadow-runs high-impact risk
    assessments against (design doc section 35, Phase 6). `None` when
    `LLM_SECONDARY_MODEL` isn't configured — the feature is opt-in, not a
    hard requirement to run the platform."""
    settings = get_settings()
    if not settings.llm_secondary_model:
        return None
    return _create_llm_adapter(settings.llm_provider, model=settings.llm_secondary_model)


__all__ = ["get_secondary_structured_llm", "get_structured_llm"]
