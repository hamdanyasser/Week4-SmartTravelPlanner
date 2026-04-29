"""Application configuration.

All environment variables enter the program through this single Settings
class. The brief calls this out explicitly: no `os.getenv` scattered
through modules, no magic strings, one source of truth.

Day 1 keeps safe local defaults so the skeleton can run without external
infrastructure. Real secrets and deployment-specific values still belong
in environment variables, not in code.
"""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "AtlasBrief"
    app_env: str = "development"
    app_debug: bool = True

    cors_allow_origins: str = Field(
        default="http://localhost:5173",
        description="Comma-separated list of allowed frontend origins.",
    )

    database_url: str = Field(
        default="postgresql+asyncpg://trippilot:change-me-local-only@db:5432/trippilot",
        description="Async SQLAlchemy URL. Used from Day 5 onward.",
    )
    embedding_provider: str = Field(
        default="deterministic",
        description="RAG embedding provider. Day 2 uses deterministic fallback.",
    )
    embedding_dimension: int = Field(
        default=384,
        description="Embedding vector size. Must match the pgvector column.",
    )
    openai_api_key: str | None = Field(
        default=None,
        description="Future real embedding provider key. Not required on Day 2.",
    )
    anthropic_api_key: str | None = Field(
        default=None,
        description="Future strong-model provider key. Not required for fallback mode.",
    )

    jwt_secret_key: str | None = Field(
        default=None,
        description="Required for issuing JWTs. Set in backend/.env.",
    )
    jwt_algorithm: str = "HS256"
    jwt_access_token_minutes: int = 120

    langchain_api_key: str | None = Field(
        default=None,
        description=(
            "LangSmith API key. When set, agent runs are traced to LangSmith "
            "automatically via the langchain env-var protocol."
        ),
    )
    langchain_project: str = "atlasbrief"
    langchain_endpoint: str = "https://api.smith.langchain.com"

    cheap_model_name: str = "deterministic-extractor"
    strong_model_name: str = "deterministic-synthesizer"
    cheap_model_provider: str = Field(
        default="auto",
        description=(
            "auto | anthropic | openai | none. 'auto' picks the cheap-class "
            "model from whichever provider key is present; 'none' forces the "
            "deterministic fallback even when keys are set."
        ),
    )
    strong_model_provider: str = Field(
        default="auto",
        description="auto | anthropic | openai | none.",
    )
    anthropic_cheap_model: str = "claude-haiku-4-5-20251001"
    anthropic_strong_model: str = "claude-sonnet-4-6"
    openai_cheap_model: str = "gpt-4o-mini"
    openai_strong_model: str = "gpt-4o"
    llm_max_output_tokens: int = 600
    llm_request_timeout_seconds: float = 30.0

    weather_live_enabled: bool = False
    weather_api_base_url: str = "https://api.open-meteo.com/v1/forecast"
    weather_timeout_seconds: float = 4.0
    weather_cache_ttl_seconds: float = Field(
        default=600.0,
        description="TTL for cached live-conditions tool responses (default 10 minutes).",
    )

    discord_webhook_url: str | None = None
    webhook_timeout_seconds: float = 4.0
    webhook_max_attempts: int = 3
    webhook_enabled: bool = True
    webhook_require_approval: bool = Field(
        default=False,
        description=(
            "If true, the webhook is NOT fired automatically after a brief "
            "completes. The user must call POST /api/v1/agent-runs/{id}/approve "
            "to release it. Useful for human-in-the-loop demos."
        ),
    )

    database_init_on_startup: bool = False

    @property
    def cors_origins_list(self) -> list[str]:
        return [
            origin.strip()
            for origin in self.cors_allow_origins.split(",")
            if origin.strip()
        ]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the singleton Settings instance."""

    return Settings()
