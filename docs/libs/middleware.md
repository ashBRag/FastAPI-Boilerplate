# libs/middleware

Two Starlette middlewares: request metrics recording, and JWT-aware logging
context binding. Both take their dependencies via constructor arguments
instead of importing project config, so they attach as-is via
`app.add_middleware(...)`.

## Setup

```python
# app/main.py
from libs.metrics import http_request_duration_seconds, http_requests_total
from libs.middleware import LoggingContextMiddleware, MetricsMiddleware

# Order matters: bind logging context before metrics/routes run, so anything
# logged further down the chain already has session_id/user_id attached.
app.add_middleware(
    LoggingContextMiddleware,
    jwt_secret_key=settings.JWT_SECRET_KEY,
    jwt_algorithm=settings.JWT_ALGORITHM,
)
app.add_middleware(
    MetricsMiddleware,
    requests_total=http_requests_total,
    request_duration_seconds=http_request_duration_seconds,
)
```

## What each one does

**`MetricsMiddleware`** - times every request and records it into the given
Prometheus `Counter`/`Histogram`, labeled by method/path/status. Records the
500 even when the handler raises, before re-raising.

**`LoggingContextMiddleware`** - on each request:
1. Clears any leftover logging context from a previous request.
2. If there's a `Bearer <token>` header, decodes it and binds `session_id`
   (from the JWT's `sub` claim) into the logging context.
3. Runs the request.
4. If a route/dependency set `request.state.user_id`, binds that too.
5. Clears the context again afterwards.

An invalid/expired token is silently ignored here (not raised) - it's the
route's own auth dependency's job to reject the request with a proper 401;
this middleware only opportunistically attaches logging context when a valid
token happens to be present.

## Usage

Nothing to call directly - once added, every log line emitted during a
request that had a valid bearer token automatically includes `session_id`:

```python
# some route/service code, no extra work needed
logger.info("order_placed", order_id=order.id)
# -> logs as: {"event": "order_placed", "order_id": 123, "session_id": "abc-session", ...}
```

To also get `user_id` attached, set it on `request.state` once you've
authenticated the user (e.g. in an auth dependency):

```python
async def get_current_user(request: Request, token: str = Depends(oauth2_scheme)):
    user = await authenticate(token)
    request.state.user_id = user.id
    return user
```
