# FastAPI Boilerplate

An async FastAPI starter with swappable infrastructure, vertical-slice modules, and plugin-ready providers.

## Stack

- **FastAPI** + Pydantic V2
- **SQLAlchemy 2.0** + Alembic migrations
- **PostgreSQL** via asyncpg · **MySQL** via aiomysql (opt-in)
- **MongoDB** via Motor (opt-in)
- **Redis** — caching (`@cache` decorator) and task broker
- **Memcached** — alternative cache/rate-limit backend (opt-in)
- **Taskiq** — async background job queue (Redis or RabbitMQ broker)
- **Kafka** — event streaming, consumer + producer (opt-in)
- **Vault** — API secret management via `Depends(get_secret_dep(...))` (opt-in)
- **AWS / LocalStack** — boto3 clients via `Depends(get_aws_client(...))` (opt-in)
- **Rate limiting** — per-path rules via Redis or Memcached

## Structure

```
src/
├── interfaces/           # FastAPI app, route mounting
├── infrastructure/       # Swappable providers
│   ├── config/           # Settings assembly, enums, loader
│   ├── database/
│   │   ├── postgresql/   # session, models, config
│   │   ├── mysql/        # session, models, config (opt-in)
│   │   └── mongodb/      # client, config (opt-in)
│   ├── cache/            # @cache decorator, Redis + Memcached backends
│   ├── rate_limit/       # Middleware, Redis + Memcached backends
│   ├── taskiq/           # Broker, worker, registry, deps
│   ├── kafka/            # Producer, @kafka_consumer decorator, lifespan
│   ├── vault/            # get_secret_dep() for API secrets
│   ├── aws/              # get_aws_client() for S3, SQS, SNS
│   └── logging/          # Structured logging, formatters, handlers
└── modules/              # Vertical-slice feature modules
    └── common/           # Shared schemas, exceptions, utils
migrations/               # Alembic migrations
tests/
```

## Quickstart

```bash
git clone https://github.com/ashBRag/FastAPI-Boilerplate
cd fastapi-boilerplate
uv sync --all-packages --all-extras

cp .env.example .env
docker compose up --build
# API at http://localhost:8000/docs
```

## Without Docker

Requires PostgreSQL and Redis running locally.

```bash
uv run alembic upgrade head
uv run fastapi dev src/interfaces/main.py

# In a second terminal
uv run taskiq worker infrastructure.taskiq.worker:default_broker
```

## Infrastructure Providers

Each provider is opt-in via `.env`. Only PostgreSQL, Redis, and Taskiq are on by default.

| Provider   | Env var           | Default | Notes                                      |
| ---------- | ----------------- | ------- | ------------------------------------------ |
| PostgreSQL | —                 | always  | Primary DB                                 |
| MySQL      | `MYSQL_ENABLED`   | `false` | Alternative DB, independent of PostgreSQL  |
| MongoDB    | `MONGODB_ENABLED` | `false` | Document store, additive                   |
| Redis      | —                 | always  | Cache + rate limit backend                 |
| Memcached  | `CACHE_BACKEND`   | `redis` | Set to `memcached` to switch               |
| Taskiq     | `TASKIQ_ENABLED`  | `true`  | Redis or RabbitMQ broker                   |
| Kafka      | `KAFKA_ENABLED`   | `false` | Consumer + producer                        |
| Vault      | `VAULT_ENABLED`   | `false` | Falls back to env vars when disabled       |
| AWS        | `AWS_ENABLED`     | `false` | LocalStack endpoint override for local dev |

## Adding a Module

1. Create the slice:

   ```bash
   mkdir -p src/modules/<feature>
   touch src/modules/<feature>/__init__.py \
         src/modules/<feature>/models.py \
         src/modules/<feature>/schemas.py \
         src/modules/<feature>/service.py \
         src/modules/<feature>/routes.py
   ```

2. Register the router in `src/interfaces/api/v1/__init__.py`:

   ```python
   from src.modules.<feature>.routes import router as <feature>_router
   router.include_router(<feature>_router, prefix="/<feature>", tags=["<feature>"])
   ```

3. Generate and apply migration (PostgreSQL):
   ```bash
   uv run alembic revision --autogenerate -m "add <feature>"
   uv run alembic upgrade head
   ```

### What each provider import looks like in a module

```python
# PostgreSQL session
from infrastructure.database.postgresql.session import async_session
async def endpoint(db: AsyncSession = Depends(async_session)): ...

# MySQL session
from infrastructure.database.mysql.session import async_session
async def endpoint(db: AsyncSession = Depends(async_session)): ...

# MongoDB
from infrastructure.database.mongodb.client import get_mongo_db
async def endpoint(db: AsyncIOMotorDatabase = Depends(get_mongo_db)): ...

# Cache decorator
from infrastructure.cache.decorator import cache
@cache(ttl=300)
async def get_items(): ...

# Background task
from infrastructure.taskiq.brokers import default_broker
@default_broker.task
async def send_email(to: str): ...

# Kafka producer
from infrastructure.kafka.producer import get_kafka_producer
async def endpoint(producer: AIOKafkaProducer = Depends(get_kafka_producer)): ...

# Kafka consumer
from infrastructure.kafka.consumer import kafka_consumer
@kafka_consumer(topic="orders")
async def handle_order(message: dict): ...

# Vault secret
from infrastructure.vault.client import get_secret_dep
async def endpoint(api_key: str = Depends(get_secret_dep("stripe", "api_key"))): ...

# AWS client
from infrastructure.aws.client import get_aws_client
async def endpoint(s3=Depends(get_aws_client("s3"))): ...
```

## Removing a Module

1. Delete `src/modules/<feature>/`
2. Remove the router registration from `src/interfaces/api/v1/__init__.py`
3. Generate and apply a migration to drop the tables:
   ```bash
   uv run alembic revision --autogenerate -m "drop <feature>"
   uv run alembic upgrade head
   ```

## Removing an Infrastructure Provider

1. Set the provider's env var to `false` (or remove it from `.env`)
2. Remove the provider's settings class from `Settings` in `src/infrastructure/config/settings.py`
3. Remove the import from `src/infrastructure/app_factory.py` lifespan if applicable
4. Any module importing that provider will raise at startup — remove those imports too

## Common Tasks

```bash
# Run migrations
uv run alembic revision --autogenerate -m "<msg>"
uv run alembic upgrade head

# Run tests
uv run pytest tests/unit
uv run pytest tests/integration   # requires Docker

# Lint and type check
uv run ruff check src/
uv run mypy src/

# Taskiq worker
uv run taskiq worker infrastructure.taskiq.worker:default_broker
```

## License

MIT
