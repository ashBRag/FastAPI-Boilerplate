"""Module for initializing the cache backends."""

from ..config import CacheBackend
from ..config.settings import get_settings
from . import REDIS_INSTALLED
from .provider import cache_provider

if REDIS_INSTALLED:
    from .backends import RedisBackend, RedisSettings


async def initialize_cache() -> None:
    settings = get_settings()

    if not settings.CACHE_ENABLED:
        return

    if settings.CACHE_BACKEND == CacheBackend.REDIS.value:
        if not REDIS_INSTALLED:
            raise ImportError("The redis package is not installed. Please install it with 'pip install redis'.")

        redis_settings = RedisSettings(
            host=settings.CACHE_REDIS_HOST,
            port=settings.CACHE_REDIS_PORT,
            db=settings.CACHE_REDIS_DB,
            password=settings.CACHE_REDIS_PASSWORD,
            connect_timeout=settings.CACHE_REDIS_CONNECT_TIMEOUT,
            pool_size=settings.CACHE_REDIS_POOL_SIZE,
        )
        redis_backend = RedisBackend(settings=redis_settings)
        cache_provider.register_backend(CacheBackend.REDIS.value, redis_backend, default=True)


async def close_cache() -> None:
    settings = get_settings()

    if not settings.CACHE_ENABLED:
        return

    if settings.CACHE_BACKEND == CacheBackend.REDIS.value and REDIS_INSTALLED:
        try:
            backend = cache_provider.get_backend(CacheBackend.REDIS.value)
            if hasattr(backend, "client") and hasattr(backend.client, "close"):
                await backend.client.close()
        except Exception:
            pass