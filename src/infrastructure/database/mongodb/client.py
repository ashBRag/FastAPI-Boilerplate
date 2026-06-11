from collections.abc import AsyncGenerator

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from ....config.settings import settings

_client: AsyncIOMotorClient | None = None


def get_mongo_client() -> AsyncIOMotorClient:
    """Return the shared Motor client, initializing it if needed.

    Motor clients are thread-safe and intended to be reused across
    the application lifetime. Do not create per-request clients.

    Returns:
        AsyncIOMotorClient: The shared MongoDB client.

    Raises:
        RuntimeError: If MongoDB is not enabled in settings.
    """
    global _client

    if not settings.MONGODB_ENABLED:
        raise RuntimeError(
            "MongoDB is not enabled. Set MONGODB_ENABLED=true in your environment."
        )

    if _client is None:
        _client = AsyncIOMotorClient(
            settings.MONGODB_URI,
            maxPoolSize=settings.MONGODB_MAX_POOL_SIZE,
            minPoolSize=settings.MONGODB_MIN_POOL_SIZE,
            connectTimeoutMS=settings.MONGODB_CONNECT_TIMEOUT_MS,
            serverSelectionTimeoutMS=settings.MONGODB_SERVER_SELECTION_TIMEOUT_MS,
        )

    return _client


async def get_mongo_db() -> AsyncGenerator[AsyncIOMotorDatabase, None]:
    """FastAPI dependency that yields the configured MongoDB database.

    Usage:
        ```python
        from fastapi import Depends
        from motor.motor_asyncio import AsyncIOMotorDatabase

        @router.get("/items")
        async def list_items(db: AsyncIOMotorDatabase = Depends(get_mongo_db)):
            return await db["items"].find().to_list(100)
        ```

    Yields:
        AsyncIOMotorDatabase: The configured MongoDB database instance.
    """
    client = get_mongo_client()
    yield client[settings.MONGODB_DB]


async def close_mongo_client() -> None:
    """Close the shared MongoDB client.

    Call this during application shutdown via FastAPI lifespan.

    Example:
        ```python
        from contextlib import asynccontextmanager

        @asynccontextmanager
        async def lifespan(app: FastAPI):
            yield
            await close_mongo_client()
        ```
    """
    global _client
    if _client is not None:
        _client.close()
        _client = None