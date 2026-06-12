from pydantic_settings import BaseSettings

from ..config.enums import CacheBackend
from ..config.loader import config


class CacheSettings(BaseSettings):
    """Cache-related settings."""

    CACHE_ENABLED: bool = config("CACHE_ENABLED", default=True, cast=bool)
    CACHE_BACKEND: str = config("CACHE_BACKEND", default=CacheBackend.MEMCACHED.value)

    CACHE_MEMCACHED_HOST: str = config("CACHE_MEMCACHED_HOST", default="localhost")
    CACHE_MEMCACHED_PORT: int = config("CACHE_MEMCACHED_PORT", default=11211, cast=int)
    CACHE_MEMCACHED_POOL_SIZE: int = config("CACHE_MEMCACHED_POOL_SIZE", default=10, cast=int)
    CACHE_MEMCACHED_CONNECT_TIMEOUT: int = config("CACHE_MEMCACHED_CONNECT_TIMEOUT", default=5, cast=int)

    CACHE_REDIS_HOST: str = config("CACHE_REDIS_HOST", default="localhost")
    CACHE_REDIS_PORT: int = config("CACHE_REDIS_PORT", default=6379, cast=int)
    CACHE_REDIS_DB: int = config("CACHE_REDIS_DB", default=0, cast=int)
    CACHE_REDIS_PASSWORD: str | None = config("CACHE_REDIS_PASSWORD", default=None)
    CACHE_REDIS_CONNECT_TIMEOUT: int = config("CACHE_REDIS_CONNECT_TIMEOUT", default=5, cast=int)
    CACHE_REDIS_POOL_SIZE: int = config("CACHE_REDIS_POOL_SIZE", default=10, cast=int)

    DEFAULT_CACHE_EXPIRATION: int = config("DEFAULT_CACHE_EXPIRATION", default=3600, cast=int)
    CLIENT_CACHE_ENABLED: bool = config("CLIENT_CACHE_ENABLED", default=True, cast=bool)
    CLIENT_CACHE_MAX_AGE: int = config("CLIENT_CACHE_MAX_AGE", default=60, cast=int)