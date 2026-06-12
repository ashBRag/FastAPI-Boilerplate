from pydantic_settings import BaseSettings

from ..config.enums import CacheBackend
from ..config.loader import config


class RateLimiterSettings(BaseSettings):
    """Rate limiter settings."""

    RATE_LIMITER_ENABLED: bool = config("RATE_LIMITER_ENABLED", default=True, cast=bool)
    RATE_LIMITER_BACKEND: str = config("RATE_LIMITER_BACKEND", default=CacheBackend.MEMCACHED.value)
    RATE_LIMITER_FAIL_OPEN: bool = config("RATE_LIMITER_FAIL_OPEN", default=True, cast=bool)

    DEFAULT_RATE_LIMIT_LIMIT: int = config("DEFAULT_RATE_LIMIT_LIMIT", default=100, cast=int)
    DEFAULT_RATE_LIMIT_PERIOD: int = config("DEFAULT_RATE_LIMIT_PERIOD", default=60, cast=int)

    RATE_LIMITER_MEMCACHED_HOST: str = config("RATE_LIMITER_MEMCACHED_HOST", default="localhost")
    RATE_LIMITER_MEMCACHED_PORT: int = config("RATE_LIMITER_MEMCACHED_PORT", default=11211, cast=int)
    RATE_LIMITER_MEMCACHED_POOL_SIZE: int = config("RATE_LIMITER_MEMCACHED_POOL_SIZE", default=10, cast=int)

    RATE_LIMITER_REDIS_HOST: str = config("RATE_LIMITER_REDIS_HOST", default="localhost")
    RATE_LIMITER_REDIS_PORT: int = config("RATE_LIMITER_REDIS_PORT", default=6379, cast=int)
    RATE_LIMITER_REDIS_DB: int = config("RATE_LIMITER_REDIS_DB", default=1, cast=int)
    RATE_LIMITER_REDIS_PASSWORD: str | None = config("RATE_LIMITER_REDIS_PASSWORD", default=None)
    RATE_LIMITER_REDIS_CONNECT_TIMEOUT: int = config("RATE_LIMITER_REDIS_CONNECT_TIMEOUT", default=5, cast=int)
    RATE_LIMITER_REDIS_POOL_SIZE: int = config("RATE_LIMITER_REDIS_POOL_SIZE", default=10, cast=int)