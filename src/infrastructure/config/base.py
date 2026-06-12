"""App-level settings that don't belong to any specific infrastructure provider."""

import logging
from enum import StrEnum

from pydantic_settings import BaseSettings

from .enums import LogFormat, LogLevel, SessionBackend
from .loader import config  # noqa: F401 — re-exported for convenience


class EnvironmentOption(StrEnum):
    PRODUCTION = "production"
    STAGING = "staging"
    DEVELOPMENT = "development"
    LOCAL = "local"


class EnvironmentSettings(BaseSettings):
    ENVIRONMENT: EnvironmentOption = config("ENVIRONMENT", default=EnvironmentOption.DEVELOPMENT, cast=EnvironmentOption)


class AppSettings(BaseSettings):
    APP_NAME: str = config("APP_NAME", default="FastAPI Boilerplate")
    APP_DESCRIPTION: str = config("APP_DESCRIPTION", default="Modular FastAPI starter")
    DEBUG: bool = config("DEBUG", default=False, cast=bool)
    VERSION: str = config("VERSION", default="0.1.0")
    CONTACT_NAME: str = config("CONTACT_NAME", default="Support")
    CONTACT_EMAIL: str = config("CONTACT_EMAIL", default="support@example.com")
    LICENSE_NAME: str = config("LICENSE_NAME", default="All rights reserved.")


class APISettings(BaseSettings):
    API_PREFIX: str = "/api"


class APIDocSettings(BaseSettings):
    ENABLE_DOCS_IN_PRODUCTION: bool = config("ENABLE_DOCS_IN_PRODUCTION", default=False, cast=bool)
    OPENAPI_PREFIX: str = config("OPENAPI_PREFIX", default="")
    DOCS_URL: str = config("DOCS_URL", default="/docs")
    REDOC_URL: str = config("REDOC_URL", default="/redoc")
    OPENAPI_URL: str = config("OPENAPI_URL", default="/openapi.json")

    API_TITLE: str = config("API_TITLE", default="")
    API_SUMMARY: str = config("API_SUMMARY", default="")
    API_DESCRIPTION: str = config("API_DESCRIPTION", default="")
    API_VERSION: str = config("API_VERSION", default="")
    API_TERMS_OF_SERVICE: str = config("API_TERMS_OF_SERVICE", default="")

    API_CONTACT_NAME: str = config("API_CONTACT_NAME", default="")
    API_CONTACT_URL: str = config("API_CONTACT_URL", default="")
    API_CONTACT_EMAIL: str = config("API_CONTACT_EMAIL", default="")

    API_LICENSE_NAME: str = config("API_LICENSE_NAME", default="")
    API_LICENSE_URL: str = config("API_LICENSE_URL", default="")
    API_LICENSE_IDENTIFIER: str = config("API_LICENSE_IDENTIFIER", default="")

    API_TAGS_METADATA: str = config("API_TAGS_METADATA", default="[]")


class AuthSettings(BaseSettings):
    SECRET_KEY: str = config("SECRET_KEY", default="insecure-secret-key-change-this")
    ALGORITHM: str = config("ALGORITHM", default="HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = config("ACCESS_TOKEN_EXPIRE_MINUTES", default=30, cast=int)
    REFRESH_TOKEN_EXPIRE_DAYS: int = config("REFRESH_TOKEN_EXPIRE_DAYS", default=7, cast=int)

    SESSION_TIMEOUT_MINUTES: int = config("SESSION_TIMEOUT_MINUTES", default=30, cast=int)
    SESSION_CLEANUP_INTERVAL_MINUTES: int = config("SESSION_CLEANUP_INTERVAL_MINUTES", default=15, cast=int)
    MAX_SESSIONS_PER_USER: int = config("MAX_SESSIONS_PER_USER", default=5, cast=int)
    SESSION_SECURE_COOKIES: bool = config("SESSION_SECURE_COOKIES", default=True, cast=bool)
    SESSION_BACKEND: str = config("SESSION_BACKEND", default=SessionBackend.REDIS.value)
    SESSION_COOKIE_MAX_AGE: int = config("SESSION_COOKIE_MAX_AGE", default=86400, cast=int)

    CSRF_ENABLED: bool = config("CSRF_ENABLED", default=True, cast=bool)
    LOGIN_MAX_ATTEMPTS: int = config("LOGIN_MAX_ATTEMPTS", default=5, cast=int)
    LOGIN_WINDOW_MINUTES: int = config("LOGIN_WINDOW_MINUTES", default=15, cast=int)

    OAUTH_GOOGLE_CLIENT_ID: str = config("OAUTH_GOOGLE_CLIENT_ID", default="")
    OAUTH_GOOGLE_CLIENT_SECRET: str = config("OAUTH_GOOGLE_CLIENT_SECRET", default="")
    OAUTH_GITHUB_CLIENT_ID: str = config("OAUTH_GITHUB_CLIENT_ID", default="")
    OAUTH_GITHUB_CLIENT_SECRET: str = config("OAUTH_GITHUB_CLIENT_SECRET", default="")
    OAUTH_REDIRECT_BASE_URL: str = config("OAUTH_REDIRECT_BASE_URL", default="http://localhost:8000")


class AdminSettings(BaseSettings):
    ADMIN_NAME: str = config("ADMIN_NAME", default="")
    ADMIN_EMAIL: str = config("ADMIN_EMAIL", default="")
    ADMIN_USERNAME: str = config("ADMIN_USERNAME", default="")
    ADMIN_PASSWORD: str = config("ADMIN_PASSWORD", default="")
    DEFAULT_TIER_NAME: str = config("DEFAULT_TIER_NAME", default="free")


class SQLAdminSettings(BaseSettings):
    ADMIN_ENABLED: bool = config("ADMIN_ENABLED", default=True, cast=bool)


class SecuritySettings(BaseSettings):
    PRODUCTION_SECURITY_VALIDATION_ENABLED: bool = config("PRODUCTION_SECURITY_VALIDATION_ENABLED", default=True, cast=bool)
    PRODUCTION_SECURITY_STRICT_MODE: bool = config("PRODUCTION_SECURITY_STRICT_MODE", default=False, cast=bool)
    SECURITY_HEADERS_ENABLED: bool = config("SECURITY_HEADERS_ENABLED", default=True, cast=bool)


class LoggingSettings(BaseSettings):
    LOG_LEVEL: str = config("LOG_LEVEL", default=LogLevel.INFO.value)
    LOG_FORMAT: str = config("LOG_FORMAT", default=LogFormat.STRUCTURED.value)

    LOG_CONSOLE_ENABLED: bool = config("LOG_CONSOLE_ENABLED", default=True, cast=bool)
    LOG_FILE_ENABLED: bool = config("LOG_FILE_ENABLED", default=False, cast=bool)
    LOG_FILE_PATH: str = config("LOG_FILE_PATH", default="logs/app.log")
    LOG_FILE_MAX_SIZE: int = config("LOG_FILE_MAX_SIZE", default=10485760, cast=int)
    LOG_FILE_BACKUP_COUNT: int = config("LOG_FILE_BACKUP_COUNT", default=5, cast=int)

    LOG_CORRELATION_ID: bool = config("LOG_CORRELATION_ID", default=True, cast=bool)
    LOG_STRUCTURED_CONTEXT: bool = config("LOG_STRUCTURED_CONTEXT", default=True, cast=bool)
    LOG_PERFORMANCE_METRICS: bool = config("LOG_PERFORMANCE_METRICS", default=False, cast=bool)
    LOG_SQL_QUERIES: bool = config("LOG_SQL_QUERIES", default=False, cast=bool)
    LOG_INCLUDE_STACKTRACE: bool = config("LOG_INCLUDE_STACKTRACE", default=True, cast=bool)
    LOG_DEVELOPMENT_VERBOSE: bool = config("LOG_DEVELOPMENT_VERBOSE", default=True, cast=bool)
    LOG_PRODUCTION_OPTIMIZE: bool = config("LOG_PRODUCTION_OPTIMIZE", default=True, cast=bool)

    @property
    def LOG_LEVEL_INT(self) -> int:
        level_map = {
            LogLevel.DEBUG.value: logging.DEBUG,
            LogLevel.INFO.value: logging.INFO,
            LogLevel.WARNING.value: logging.WARNING,
            LogLevel.ERROR.value: logging.ERROR,
            LogLevel.CRITICAL.value: logging.CRITICAL,
        }
        return level_map.get(self.LOG_LEVEL.upper(), logging.INFO)


class CORSSettings(BaseSettings):
    CORS_ENABLED: bool = config("CORS_ENABLED", default=True, cast=bool)
    CORS_ORIGINS: str = config("CORS_ORIGINS", default="*")
    CORS_ALLOW_CREDENTIALS: bool = config("CORS_ALLOW_CREDENTIALS", default=True, cast=bool)
    CORS_ALLOW_METHODS: str = config("CORS_ALLOW_METHODS", default="*")
    CORS_ALLOW_HEADERS: str = config("CORS_ALLOW_HEADERS", default="*")

    @property
    def CORS_ORIGINS_LIST(self) -> list[str]:
        if not self.CORS_ORIGINS:
            return ["*"]
        return [x.strip() for x in self.CORS_ORIGINS.split(",") if x.strip()]


class CompressionSettings(BaseSettings):
    GZIP_ENABLED: bool = config("GZIP_ENABLED", default=True, cast=bool)
    GZIP_MINIMUM_SIZE: int = config("GZIP_MINIMUM_SIZE", default=1000, cast=int)