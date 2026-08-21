# libs/limiter

A one-function factory around `slowapi.Limiter`, keyed by remote IP address.

## Setup

```python
# app/main.py
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from libs.limiter import build_limiter

limiter = build_limiter(settings.RATE_LIMIT_DEFAULT)  # e.g. ["200 per day", "50 per hour"]

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
```

## Usage

Apply the default limit implicitly (just having `app.state.limiter` set is
enough), or override per-route:

```python
@app.get("/health")
@limiter.limit("20 per minute")
async def health_check(request: Request):
    ...
```

Every `@limiter.limit(...)`-decorated route **must** accept `request: Request`
as a parameter - slowapi reads the client IP from it.

A request that exceeds its limit gets a `429 Too Many Requests` automatically,
handled by the registered `_rate_limit_exceeded_handler`.

## Per-route limits from settings

This project's `app/core/config.py` keeps per-route limits in one dict so
they're easy to find/tune:

```python
# app/core/config.py
RATE_LIMIT_ENDPOINTS: dict[str, list[str]] = {
    "root": ["60 per minute"],
    "health": ["20 per minute"],
}

# app/main.py
@app.get("/")
@limiter.limit(settings.RATE_LIMIT_ENDPOINTS["root"][0])
async def root(request: Request):
    ...
```
