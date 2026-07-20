from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Process-wide configuration, sourced from environment variables.

    See `.env.example` for the full list of supported variables.
    """

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: Literal["development", "test", "staging", "production"] = "development"
    app_secret_key: str = "change-me-to-a-random-secret"

    database_url: str = "postgresql+asyncpg://mei:mei@localhost:5432/mei"
    redis_url: str = "redis://localhost:6379/0"

    s3_endpoint_url: str = "http://localhost:9000"
    s3_access_key: str = "mei"
    s3_secret_key: str = "mei-secret-key"
    s3_bucket: str = "mei-raw"

    llm_provider: str = "openai"
    llm_model: str = "gpt-4o-mini"
    llm_api_key: str = ""

    jwt_issuer: str = "mei-platform"
    jwt_audience: str = "mei-clients"
    jwt_access_token_ttl_seconds: int = Field(default=3600, gt=0)

    hermes_api_key: str = ""

    # Hostnames the SSRF policy in infrastructure/collection permits even
    # though they resolve to a private/loopback/link-local address (e.g. an
    # internal mirror). Empty by default per section 10.3 of the design.
    collector_allowed_private_hosts: list[str] = Field(default_factory=list)

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()
