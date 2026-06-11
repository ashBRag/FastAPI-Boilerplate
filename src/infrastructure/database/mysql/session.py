from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, MappedAsDataclass

from ....config.settings import settings

engine = create_async_engine(
    settings.MYSQL_URL,
    echo=False,
    future=True,
    pool_size=settings.MYSQL_POOL_SIZE,
    max_overflow=settings.MYSQL_MAX_OVERFLOW,
    connect_args={"connect_timeout": settings.MYSQL_CONNECT_TIMEOUT},
)

local_session = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase, MappedAsDataclass):
    """Base class for all MySQL models.

    Mirrors the PostgreSQL Base class. Models targeting MySQL
    should inherit from this Base, not the PostgreSQL one.

    Example:
        ```python
        from sqlalchemy.orm import Mapped, mapped_column
        from sqlalchemy import String

        class Product(Base):
            __tablename__ = "products"

            id: Mapped[int] = mapped_column(primary_key=True)
            name: Mapped[str] = mapped_column(String(100))
        ```
    """

    pass


async def async_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency for MySQL session management.

    Usage:
        ```python
        from fastapi import Depends
        from sqlalchemy.ext.asyncio import AsyncSession

        @router.get("/products")
        async def list_products(db: AsyncSession = Depends(async_session)):
            ...
        ```

    Yields:
        AsyncSession: A configured async MySQL session.
    """
    async with local_session() as db:
        yield db


async def create_tables() -> None:
    """Create all MySQL tables defined under this Base.

    For production use Alembic migrations instead.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)