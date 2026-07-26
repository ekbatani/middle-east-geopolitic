import pytest
from unittest.mock import patch

from mei.infrastructure.llm.factory import get_secondary_structured_llm, get_structured_llm
from mei.infrastructure.llm.openai_adapter import OpenAIStructuredLLM
from mei.shared.config import Settings, get_settings


@pytest.fixture(autouse=True)
def _clear_settings_cache() -> None:
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def test_openai_provider_default() -> None:
    settings = Settings(llm_provider="openai", llm_api_key="test-key")
    with patch("mei.infrastructure.llm.factory.get_settings", return_value=settings):
        adapter = get_structured_llm()
        assert isinstance(adapter, OpenAIStructuredLLM)
        assert str(adapter._client.base_url).rstrip("/") == "https://api.openai.com/v1"


def test_openrouter_provider() -> None:
    settings = Settings(llm_provider="openrouter", llm_api_key="test-key")
    with patch("mei.infrastructure.llm.factory.get_settings", return_value=settings):
        adapter = get_structured_llm()
        assert isinstance(adapter, OpenAIStructuredLLM)
        assert str(adapter._client.base_url).rstrip("/") == "https://openrouter.ai/api/v1"


@pytest.mark.parametrize("provider", ["opencode_go", "opencode", "opencode-go"])
def test_opencode_go_provider(provider: str) -> None:
    settings = Settings(llm_provider=provider, llm_api_key="test-key")
    with patch("mei.infrastructure.llm.factory.get_settings", return_value=settings):
        adapter = get_structured_llm()
        assert isinstance(adapter, OpenAIStructuredLLM)
        assert str(adapter._client.base_url).rstrip("/") == "https://api.opencode.ai/v1"


@pytest.mark.parametrize("provider", ["nvidia_build", "nvidia", "nvidia-build"])
def test_nvidia_build_provider(provider: str) -> None:
    settings = Settings(llm_provider=provider, llm_api_key="test-key")
    with patch("mei.infrastructure.llm.factory.get_settings", return_value=settings):
        adapter = get_structured_llm()
        assert isinstance(adapter, OpenAIStructuredLLM)
        assert str(adapter._client.base_url).rstrip("/") == "https://integrate.api.nvidia.com/v1"


def test_ollama_provider() -> None:
    settings = Settings(llm_provider="ollama", llm_api_key="test-key")
    with patch("mei.infrastructure.llm.factory.get_settings", return_value=settings):
        adapter = get_structured_llm()
        assert isinstance(adapter, OpenAIStructuredLLM)
        assert str(adapter._client.base_url).rstrip("/") == "http://localhost:11434/v1"


def test_custom_base_url_override() -> None:
    settings = Settings(
        llm_provider="openrouter",
        llm_api_key="test-key",
        llm_base_url="https://custom.gateway.org/v1",
    )
    with patch("mei.infrastructure.llm.factory.get_settings", return_value=settings):
        adapter = get_structured_llm()
        assert isinstance(adapter, OpenAIStructuredLLM)
        assert str(adapter._client.base_url).rstrip("/") == "https://custom.gateway.org/v1"


def test_unsupported_provider_raises_value_error() -> None:
    settings = Settings(llm_provider="unknown_provider", llm_api_key="test-key")
    with patch("mei.infrastructure.llm.factory.get_settings", return_value=settings):
        with pytest.raises(ValueError, match="Unsupported LLM provider"):
            get_structured_llm()


def test_secondary_structured_llm_resolution() -> None:
    settings = Settings(
        llm_provider="nvidia_build",
        llm_api_key="test-key",
        llm_secondary_model="meta/llama-3.3-70b-instruct",
    )
    with patch("mei.infrastructure.llm.factory.get_settings", return_value=settings):
        adapter = get_secondary_structured_llm()
        assert adapter is not None
        assert isinstance(adapter, OpenAIStructuredLLM)
        assert adapter._model == "meta/llama-3.3-70b-instruct"
        assert str(adapter._client.base_url).rstrip("/") == "https://integrate.api.nvidia.com/v1"
