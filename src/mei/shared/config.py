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

    # Multi-model review (design doc section 35, Phase 6): a second model
    # used only to shadow-check high-impact risk assessments. Empty disables
    # the feature entirely, matching the `llm_api_key`-empty precedent.
    llm_secondary_model: str = ""
    multi_model_review_score_delta_threshold: int = Field(default=15, ge=1, le=100)
    multi_model_review_agreement_tolerance: int = Field(default=5, ge=0, le=100)

    jwt_issuer: str = "mei-platform"
    jwt_audience: str = "mei-clients"
    jwt_access_token_ttl_seconds: int = Field(default=3600, gt=0)

    hermes_api_key: str = ""
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""

    # Hostnames the SSRF policy in infrastructure/collection permits even
    # though they resolve to a private/loopback/link-local address (e.g. an
    # internal mirror). Empty by default per section 10.3 of the design.
    collector_allowed_private_hosts: list[str] = Field(default_factory=list)

    # Entity resolution thresholds (RapidFuzz 0-100 score) per section 12.2:
    # at/above `auto` the match is applied automatically; below `review` no
    # candidate is confident enough to surface; in between, the best
    # candidates are queued for analyst review rather than guessed.
    entity_resolution_auto_threshold: float = Field(default=92.0, ge=0, le=100)
    entity_resolution_review_threshold: float = Field(default=75.0, ge=0, le=100)

    translation_target_language: str = "en"

    # Window used by the event-clustering heuristic (section 15.2) to decide
    # whether a newly extracted event should reuse an existing one.
    event_dedup_window_hours: int = Field(default=48, gt=0)

    # Age threshold used by the archive_old_raw_data maintenance job.
    raw_data_retention_days: int = Field(default=180, gt=0)

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()
