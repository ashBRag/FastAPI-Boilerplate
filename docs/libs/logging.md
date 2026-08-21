# libs/logging

`structlog`-based structured logging with dual console/JSON output, plus
request-scoped context binding so fields like `session_id`/`user_id` show up
on every log line for that request without threading them through every call.

## Setup

```python
# app/main.py
from app.core.config import settings
from libs.logging import setup_logging

logger = setup_logging(settings, extra_context={"environment": settings.ENVIRONMENT.value})
```

`settings` just needs `DEBUG`, `LOG_DIR`, `LOG_LEVEL`, `LOG_FORMAT`, and
`ENVIRONMENT` (any `libs.config.BaseAppSettings` subclass satisfies this).

## Usage

```python
logger.info("user_signed_up", user_id=user.id, plan=user.plan)
logger.warning("rate_limit_close", remaining=3)
logger.error("payment_failed", order_id=order.id, error=str(exc))
```

In dev (`LOG_FORMAT=console`) this renders as colored, human-readable lines.
In staging/prod (`LOG_FORMAT=json`) it renders as one JSON object per line,
also written to `logs/<environment>-<date>.jsonl`.

## Binding request-scoped context

Used internally by `libs.middleware.LoggingContextMiddleware`, but you can
bind extra fields from anywhere during a request (e.g. inside a dependency
once you know the authenticated user):

```python
from libs.logging import bind_context

async def get_current_user(token: str = Depends(oauth2_scheme)):
    user = await authenticate(token)
    bind_context(user_id=user.id)  # now every log line in this request includes user_id
    return user
```

Every subsequent `logger.info(...)` call in that same request automatically
includes `user_id` - no need to pass it explicitly.
