# FastAPI Boilerplate

An async FastAPI starter with PostgreSQL, Redis, background jobs, caching, and rate limiting.

## Stack

- **FastAPI** + Pydantic V2
- **SQLAlchemy 2.0** + Alembic migrations
- **PostgreSQL** via asyncpg
- **Redis** — caching (`@cache` decorator) and task broker
- **Taskiq** — async background job queue
- **Rate limiting** — per-path rules via Redis

## Structure

```
fastapi-boilerplate/
|─ src/
|  ├── interfaces/        # FastAPI app, route mounting
|  ├── infrastructure/    # DB, cache, rate_limit, taskiq, config, logging
|  └── modules/           # Vertical-slice feature modules
|      └── common/        # Shared schemas, exceptions, utils
|─ migrations/            # Alembic migrations
|─ scripts/               # One-off setup scripts
|─ tests/
```

## Quickstart

```bash
git clone https://github.com/ashBRag/FastAPI-Boilerplate
cd fastapi-boilerplate
uv sync --all-packages --all-extras

# Configure env
cp .env.example .env


# Start
docker compose up --build
# API at http://localhost:8000/docs
```

## Without Docker

Requires Postgres and Redis running locally.

```bash
uv run alembic upgrade head
uv run fastapi dev src/interfaces/main.py

# In a second terminal
uv run taskiq worker infrastructure.taskiq.worker:default_broker
```

## Adding a Module

1. Create `src/modules/<feature>/`
2. Add `models.py`, `schemas.py`, `crud.py`, `service.py`, `routes.py`
3. Register the router in `src/interfaces/api/v1/__init__.py`
4. Generate and apply migration:
   ```bash
   uv run alembic revision --autogenerate -m "add <feature>"
   uv run alembic upgrade head
   ```

## Common Tasks

```bash
# Audit .env
uv run bp env validate

# Run migrations
uv run alembic revision --autogenerate -m "<msg>" && uv run alembic upgrade head

# Run tests
uv run pytest tests/unit
uv run pytest tests/integration   # requires Docker
```

## License

MIT
