"""
Application configuration.

Settings are loaded from environment variables (and an optional .env file)
using pydantic-settings. Only Phase 1 settings are defined here — settings
needed for later phases (DB, JWT, external providers, LLM) will be added
in their respective phases.
"""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- App metadata ---
    APP_NAME: str = "Ocean Agentic AI"
    APP_VERSION: str = "0.1.0"
    APP_DESCRIPTION: str = (
        "Backend for a marine ecosystem intelligence platform combining "
        "oceanographic, weather, tide, wave and satellite data with "
        "specialized AI agents."
    )

    # --- Environment ---
    ENVIRONMENT: str = "development"  # development | staging | production
    DEBUG: bool = True

    # --- Logging ---
    LOG_LEVEL: str = "INFO"


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance (avoids re-parsing env on every call)."""
    return Settings()
