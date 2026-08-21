# libs/* documentation

Each reusable package under `libs/` has a doc here with setup + usage
examples. Each package is self-contained (dependencies passed in via
constructor/function arguments rather than importing this project's config),
so any one of them can be copied into another project on its own.

| Doc | Package | Provides |
|---|---|---|
| [config.md](./config.md) | `libs/config` | `BaseAppSettings`, `Environment` |
| [logging.md](./logging.md) | `libs/logging` | `setup_logging`, `bind_context`/`clear_context` |
| [metrics.md](./metrics.md) | `libs/metrics` | Prometheus counters/histogram + `/metrics` route |
| [middleware.md](./middleware.md) | `libs/middleware` | `MetricsMiddleware`, `LoggingContextMiddleware` |
| [limiter.md](./limiter.md) | `libs/limiter` | `build_limiter` |
| [auth.md](./auth.md) | `libs/auth` | `verify_token` |
| [sanitization.md](./sanitization.md) | `libs/sanitization` | `sanitize_string`/`sanitize_dict`/`sanitize_list`/`sanitize_email` |
| [errors.md](./errors.md) | `libs/errors` | `AppError` hierarchy + `register_exception_handlers` |
| [http.md](./http.md) | `libs/http` | `build_http_client` |
| [db.md](./db.md) | `libs/db` | `Database`, `DatabaseSettings`, `TimestampedModel` |
| [redis.md](./redis.md) | `libs/redis` | `Cache`, `RedisSettings` |
| [kafka.md](./kafka.md) | `libs/kafka` | `Producer`, `Consumer`, `KafkaSettings` |
| [aws.md](./aws.md) | `libs/aws` | `S3Client`, `SqsClient`, `AwsSettings` |
| [streaming.md](./streaming.md) | `libs/streaming` | `SseEvent`, `sse_response`, `ndjson_response`, `text_chunk_response` |
