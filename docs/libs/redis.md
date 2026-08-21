# libs/redis

An async Redis connection wrapper (redis-py's `redis.asyncio` client) with
connect/disconnect for app lifespan and a non-raising health check.

## Setup

```python
# app/main.py
from libs.redis import Cache, RedisSettings

cache = Cache(
    RedisSettings(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        db=settings.REDIS_DB,
        password=settings.REDIS_PASSWORD,
    )
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        await cache.connect()
    except Exception as exc:
        logger.error("redis_connect_failed", error=str(exc))
    yield
    await cache.disconnect()
```

## Usage

The underlying `redis.asyncio.Redis` client is exposed as `cache.client` -
use it directly for any Redis command:

```python
# set with a 60s TTL
await cache.client.set("session:abc123", "user-42", ex=60)

# get
value = await cache.client.get("session:abc123")  # -> "user-42" or None

# increment a counter
await cache.client.incr("page_views")

# hash / list / set operations all work the same way
await cache.client.hset("user:42", mapping={"name": "Bob", "plan": "pro"})
```

## Health check

```python
@app.get("/health")
async def health_check():
    redis_healthy = await cache.health_check()  # never raises, returns True/False
```

## Caching a function result (simple pattern)

```python
import json

async def get_widget_cached(widget_id: int) -> dict:
    cache_key = f"widget:{widget_id}"
    cached = await cache.client.get(cache_key)
    if cached:
        return json.loads(cached)

    widget = await widgets_service.find(widget_id)
    await cache.client.set(cache_key, json.dumps(widget), ex=300)
    return widget
```

## Notes

- `decode_responses=True` is set by default, so string commands return `str`,
  not `bytes`.
- Instantiate `Cache` more than once if you need to talk to two different
  Redis instances (e.g. a cache vs. a session store).
