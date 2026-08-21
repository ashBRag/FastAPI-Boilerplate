# libs/http

An async HTTP client factory built on `httpx.AsyncClient`, with retry/backoff
(via `tenacity`) wired in for transient failures.

## Usage

```python
from libs.http import build_http_client

client = build_http_client(base_url="https://api.example.com", logger=logger)

response = await client.get("/things/123")
response.raise_for_status()
data = response.json()

await client.aclose()
```

As an async context manager (recommended - guarantees cleanup):

```python
async with build_http_client(base_url="https://api.example.com") as client:
    response = await client.post("/things", json={"name": "widget"})
```

## What gets retried

- Connection errors / timeouts (`httpx.TransportError`) - always retried.
- 5xx responses (500, 502, 503, 504) - retried.
- 4xx responses - **never** retried; these are treated as permanent failures
  (a bad request won't succeed by resending it).

Retries use exponential backoff (0.5s, 1s, 2s, ... capped at 5s) and raise the
original exception once `max_attempts` is exhausted.

## Options

```python
client = build_http_client(
    base_url="https://api.example.com",
    timeout=5.0,        # seconds, applied to connect/read/write/pool
    max_attempts=5,      # total attempts including the first
    logger=logger,       # optional; logs a warning before each retry
    headers={"Authorization": f"Bearer {token}"},  # passed straight to httpx.AsyncClient
)
```

## Typical usage: calling a downstream service

```python
# app/services/payments_client.py
from libs.http import build_http_client
from app.core.config import settings
from app.core.logging import logger  # or wherever setup_logging()'s logger lives

payments_client = build_http_client(
    base_url=settings.PAYMENTS_SERVICE_URL,
    timeout=5.0,
    logger=logger,
)

async def charge_card(order_id: str, amount_cents: int) -> dict:
    response = await payments_client.post(
        "/charges", json={"order_id": order_id, "amount_cents": amount_cents}
    )
    response.raise_for_status()
    return response.json()
```
