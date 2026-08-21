"""Project-specific application settings.

Generic env/logging/rate-limit machinery lives in libs.config;
this file only adds fields and defaults specific to *this* project.
"""

from libs.config import BaseAppSettings, Environment

__all__ = ["Environment", "settings"]


class Settings(BaseAppSettings):
    """This project's settings: adds identity/API fields on top of the base."""

    PROJECT_NAME: str = "FastAPI Template"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = "A production-ready FastAPI template"
    API_V1_STR: str = "/api/v1"

    # Per-route rate limits; "default" (from BaseAppSettings.RATE_LIMIT_DEFAULT)
    # applies to any route not listed here.
    RATE_LIMIT_ENDPOINTS: dict[str, list[str]] = {
        "root": ["60 per minute"],
        "health": ["20 per minute"],
    }

    # Postgres connection (see libs/db for the engine/session built from these).
    POSTGRES_HOST: str = "db"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "mydb"
    POSTGRES_USER: str = "myuser"
    POSTGRES_PASSWORD: str = ""
    POSTGRES_POOL_SIZE: int = 5
    POSTGRES_MAX_OVERFLOW: int = 10


# Constructed once at import time and shared app-wide.
settings = Settings().apply_environment_defaults()
