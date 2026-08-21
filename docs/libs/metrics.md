# libs/metrics

Standard Prometheus HTTP request counters/timers, plus a `/metrics` route
ready for Prometheus to scrape.

## Setup

```python
# app/main.py
from libs.metrics import setup_metrics

app = FastAPI(...)
setup_metrics(app)  # mounts GET /metrics
```

Pair it with `libs.middleware.MetricsMiddleware` to actually record request
metrics (see [middleware.md](./middleware.md)):

```python
from libs.metrics import http_request_duration_seconds, http_requests_total
from libs.middleware import MetricsMiddleware

app.add_middleware(
    MetricsMiddleware,
    requests_total=http_requests_total,
    request_duration_seconds=http_request_duration_seconds,
)
```

## Usage

`curl http://localhost:8000/metrics` returns standard Prometheus exposition
format:

```
# HELP http_requests_total Total number of HTTP requests
# TYPE http_requests_total counter
http_requests_total{endpoint="/",method="GET",status="200"} 1.0
```

## Adding your own metrics

`libs.metrics` only defines generic HTTP metrics. Define business-specific
ones in your own project and they'll be picked up automatically by the same
`/metrics` route (Prometheus client's registry is global):

```python
# app/core/metrics.py
from prometheus_client import Counter

orders_processed = Counter("orders_processed_total", "Total orders processed")

# elsewhere:
orders_processed.inc()
```

There's also a generic `db_connections` gauge in `libs.metrics` you can update
from your own connection-pool code:

```python
from libs.metrics import db_connections

db_connections.set(pool.size)
```
