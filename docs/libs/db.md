# libs/db

Async SQLAlchemy/SQLModel database wiring: engine, session factory,
connect/disconnect for app lifespan, a FastAPI session dependency, and a
non-raising health check. Plus `TimestampedModel`, a common SQLModel base.

## Setup

```python
# app/main.py
from contextlib import asynccontextmanager
from libs.db import Database, DatabaseSettings

db = Database(
    DatabaseSettings(
        host=settings.POSTGRES_HOST,
        port=settings.POSTGRES_PORT,
        database=settings.POSTGRES_DB,
        user=settings.POSTGRES_USER,
        password=settings.POSTGRES_PASSWORD,
        pool_size=settings.POSTGRES_POOL_SIZE,
        max_overflow=settings.POSTGRES_MAX_OVERFLOW,
    )
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        await db.connect()
    except Exception as exc:
        logger.error("database_connect_failed", error=str(exc))
    yield
    await db.disconnect()

app = FastAPI(lifespan=lifespan)
```

## Usage - as a FastAPI dependency

```python
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

@app.get("/widgets/{widget_id}")
async def get_widget(widget_id: int, session: AsyncSession = Depends(db.get_session)):
    result = await session.execute(select(Widget).where(Widget.id == widget_id))
    return result.scalar_one_or_none()
```

## Usage - health check

```python
@app.get("/health")
async def health_check():
    db_healthy = await db.health_check()  # never raises, returns True/False
    return {"status": "healthy" if db_healthy else "degraded"}
```

## Defining models

Subclass `TimestampedModel` instead of `SQLModel` directly to get
`created_at` for free:

```python
# app/models/widget.py
from sqlmodel import Field
from app.models.base import BaseModel  # re-exports libs.db.TimestampedModel

class Widget(BaseModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str
```

## Notes

- Connection string is built as `postgresql+psycopg://...` (psycopg3, native
  async support - no extra async driver package needed).
- `connect()` runs `SELECT 1` at startup so misconfiguration fails fast
  instead of surfacing on the first real request.
- If you need to talk to two different Postgres instances, just instantiate
  `Database` twice with different `DatabaseSettings`.
