"""Reusable async Redis connection wrapper (redis-py's async client).

Generic and reusable: `Cache` takes a `RedisSettings` value object instead
of importing any project's settings class, so it can be reused as-is in
another project.

Usage in a project's own main.py:

    from libs.redis import Cache, RedisSettings

    cache = Cache(RedisSettings(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        password=settings.REDIS_PASSWORD,
        db=settings.REDIS_DB,
    ))

    # in the FastAPI lifespan:
    await cache.connect()
    ...
    await cache.disconnect()

    # anywhere else:
    await cache.client.set("key", "value", ex=60)
"""

from dataclasses import dataclass

import redis.asyncio as redis


@dataclass(frozen=True)
class RedisSettings:
    """Connection parameters for a Redis instance.

    A plain value object (not a pydantic BaseSettings) so libs/redis has
    zero dependency on any particular settings/config library - the caller
    reads these values from wherever it likes and passes them in.
    """

    host: str
    port: int = 6379
    db: int = 0
    password: str | None = None
    max_connections: int = 10

    def to_url(self) -> str:
        """Build a redis:// URL from these settings."""
        auth = f":{self.password}@" if self.password else ""
        return f"redis://{auth}{self.host}:{self.port}/{self.db}"


class Cache:
    """Owns the async Redis connection pool for one Redis instance.

    Kept as a class (rather than module-level globals) so a project can
    instantiate more than one Cache if it ever needs to talk to two
    different Redis instances (e.g. cache vs. session store).
    """

    def __init__(self, settings: RedisSettings):
        """Build the connection pool eagerly; no network call happens until first use."""
        self._settings = settings
        self.client: redis.Redis = redis.from_url(
            settings.to_url(),
            max_connections=settings.max_connections,
            decode_responses=True,
        )

    async def connect(self) -> None:
        """Verify connectivity at startup so config mistakes fail fast, not on first request."""
        await self.client.ping()

    async def disconnect(self) -> None:
        """Close the connection pool (call this on app shutdown)."""
        await self.client.aclose()

    async def health_check(self) -> bool:
        """Return True if PING succeeds, False on any error.

        Used by /health so it never raises - a Redis outage should degrade
        the health response, not crash the health endpoint itself.
        """
        try:
            return bool(await self.client.ping())
        except Exception:
            return False
