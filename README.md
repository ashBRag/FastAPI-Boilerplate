# FastAPI Boilerplate

A lightweight FastAPI service boilerplate: structured logging, Prometheus metrics,
rate limiting, JWT-aware middleware, consistent API error handling, and async
clients for Postgres, Redis, Kafka, and AWS (S3/SQS) - all as small, independently
reusable packages under `libs/`.

Postgres, Prometheus, and Grafana are expected to run externally (e.g. in their
own docker-compose stack on a shared `backend-internal` network) - this repo only
runs the API itself.

## Project layout

```
app/                    # This project's code only
  main.py               # Wires libs/* together with this project's settings/routes
  core/config.py        # Settings subclass (adds PROJECT_NAME, rate limits, POSTGRES_*, ...)
  api/v1/api.py         # API router - add your endpoints here
  models/               # SQLModel table models (subclass libs.db.TimestampedModel)
  schemas/              # Pydantic request/response schemas
  services/             # Business logic

libs/                   # Reusable, project-agnostic building blocks.
  config/               #   Each folder is self-contained enough to copy into
  logging/              #   another project (or split into its own repo) on its own.
  metrics/              #   Code lives in <folder>/base.py; __init__.py re-exports it.
  middleware/
  limiter/
  auth/
  sanitization/
  errors/
  http/
  db/
  redis/
  kafka/
  aws/
```

## Requirements

- Python >= 3.14
- [uv](https://docs.astral.sh/uv/)
- Docker (optional, for containerized runs)

## Setup

```bash
make install                        # uv sync
cp .env.example .env.development    # fill in real values (JWT secret, Postgres, etc.)
```

## Running

```bash
make dev     # uvicorn with reload, port 8000
make prod    # uvicorn, no reload
```

Or directly:

```bash
uv run uvicorn app.main:app --reload --port 8000
```

Check it's up:

- `GET /` - basic service info
- `GET /health` - liveness + Postgres connectivity (`degraded`/503 if the DB is unreachable)
- `GET /docs` - Swagger UI
- `GET /metrics` - Prometheus scrape endpoint

## Docker

The app container joins the external `backend-internal` network so it can reach
Postgres/Prometheus/Grafana running in their own stack.

```bash
make docker-up     # creates backend-internal if missing, builds, starts (ENV=development by default)
make docker-logs
make docker-down
```

Pass `ENV=staging` / `ENV=production` to target a different `.env.<ENV>` file.

## Configuration

Settings are loaded via `pydantic-settings` from `.env.<APP_ENV>` (falling back to
`.env.local` / `.env`), with environment-specific defaults for things like log
level and rate limits applied on top - see `libs/config/base.py` for the
resolution order and `app/core/config.py` for this project's fields.

See `.env.example` for the full list of variables, including the optional ones
for Redis/Kafka/AWS.

## The `libs/` packages

Each package takes its dependencies (settings, loggers, metric objects) as
constructor/function arguments rather than importing this project's config
directly - so any one of them can be copied into another project, or pulled out
into its own repo, without touching the rest.

| Package | Provides | Docs |
|---|---|---|
| `config` | `BaseAppSettings`, `Environment` - env-file resolution + per-environment defaults | [docs/libs/config.md](./docs/libs/config.md) |
| `logging` | `setup_logging`, `bind_context`/`clear_context` - structlog with request-scoped context | [docs/libs/logging.md](./docs/libs/logging.md) |
| `metrics` | Prometheus counters/histogram + `/metrics` route | [docs/libs/metrics.md](./docs/libs/metrics.md) |
| `middleware` | `MetricsMiddleware`, `LoggingContextMiddleware` | [docs/libs/middleware.md](./docs/libs/middleware.md) |
| `limiter` | `build_limiter` - slowapi rate limiter factory | [docs/libs/limiter.md](./docs/libs/limiter.md) |
| `auth` | `verify_token` - JWT verification | [docs/libs/auth.md](./docs/libs/auth.md) |
| `sanitization` | `sanitize_string`/`sanitize_dict`/`sanitize_list`/`sanitize_email` | [docs/libs/sanitization.md](./docs/libs/sanitization.md) |
| `errors` | `AppError` hierarchy + `register_exception_handlers` - consistent `{"error": {...}}` responses | [docs/libs/errors.md](./docs/libs/errors.md) |
| `http` | `build_http_client` - async httpx client with retry/backoff on 5xx/network errors | [docs/libs/http.md](./docs/libs/http.md) |
| `db` | `Database`, `DatabaseSettings`, `TimestampedModel` - async Postgres engine/session/health check | [docs/libs/db.md](./docs/libs/db.md) |
| `redis` | `Cache`, `RedisSettings` - async Redis client/health check | [docs/libs/redis.md](./docs/libs/redis.md) |
| `kafka` | `Producer`, `Consumer`, `KafkaSettings` - aiokafka wrappers | [docs/libs/kafka.md](./docs/libs/kafka.md) |
| `aws` | `S3Client`, `SqsClient`, `AwsSettings` - aioboto3 wrappers (S3 and SQS only) | [docs/libs/aws.md](./docs/libs/aws.md) |

Only `db` is currently wired into `app/main.py` (startup connect + `/health`
check). Wire up `redis`/`kafka`/`aws` in your own project the same way, once you
actually need them.

## Linting & tests

```bash
make lint     # ruff check
make format   # ruff format
make test     # pytest
```
