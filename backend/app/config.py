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
