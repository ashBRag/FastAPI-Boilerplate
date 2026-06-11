import os
import secrets
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest
import pytest_asyncio
import redis as syncredis
import redis.asyncio as aioredis
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from testcontainers.core.docker_client import DockerClient

# mypy: disable-error-code="import-untyped"
from testcontainers.postgres import PostgresContainer
from src.infrastructure.config.settings import Settings, get_settings
from src.infrastructure.database.postgresql.session import Base, async_session
from src.interfaces.main import app

os.environ["SQLITE_URI"] = ":memory:"
os.environ["SQLITE_ASYNC_PREFIX"] = "sqlite+aiosqlite:///"
os.environ["SECRET_KEY"] = "test_secret_key_for_tests"

TEST_DATABASE_URL = get_settings().DATABASE_URL

backend_dir = Path(__file__).parent.parent
sys.path.append(str(backend_dir))


def is_docker_running() -> bool:
    try:
        DockerClient()
        return True
    except Exception:
        return False


@pytest_asyncio.fixture(scope="session")
async def pg_container():
    """Create a PostgreSQL container for testing."""
    if not is_docker_running():
        pytest.skip("Docker is required, but not running")

    with PostgresContainer() as pg:
        yield pg


@pytest_asyncio.fixture(scope="function")
async def test_db_url(pg_container):
    """Create a proper asyncpg URL for PostgreSQL."""
    host = pg_container.get_container_host_ip()
    port_to_expose = 5432
    if hasattr(pg_container, "port_to_expose"):
        port_to_expose = pg_container.port_to_expose
    port = pg_container.get_exposed_port(port_to_expose)

    db = "test"
    user = "test"
    password = "test"
    if hasattr(pg_container, "POSTGRES_USER"):
        user = pg_container.POSTGRES_USER
    if hasattr(pg_container, "POSTGRES_PASSWORD"):
        password = pg_container.POSTGRES_PASSWORD
    if hasattr(pg_container, "POSTGRES_DB"):
        db = pg_container.POSTGRES_DB

    return f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{db}"


@pytest.fixture
def mock_rate_limit_settings_fail_open():
    """Mock settings with fail_open=True for rate limiter tests."""
    settings = MagicMock(spec=Settings)
    settings.RATE_LIMITER_ENABLED = True
    settings.RATE_LIMITER_FAIL_OPEN = True
    settings.DEFAULT_RATE_LIMIT_LIMIT = 100
    settings.DEFAULT_RATE_LIMIT_PERIOD = 60
    return settings


@pytest.fixture
def mock_rate_limit_settings_fail_closed():
    """Mock settings with fail_open=False for rate limiter tests."""
    settings = MagicMock(spec=Settings)
    settings.RATE_LIMITER_ENABLED = True
    settings.RATE_LIMITER_FAIL_OPEN = False
    settings.DEFAULT_RATE_LIMIT_LIMIT = 100
    settings.DEFAULT_RATE_LIMIT_PERIOD = 60
    return settings


@pytest.fixture(autouse=True)
def patch_redis_pipeline_for_tests(monkeypatch):
    class MockPipeline:
        def __init__(self, *args, **kwargs):
            self.commands = []

        async def aexecute(self, *args, **kwargs):
            return [True for _ in self.commands]

        def set(self, *args, **kwargs):
            self.commands.append(("set", args, kwargs))
            return self

        def sadd(self, *args, **kwargs):
            self.commands.append(("sadd", args, kwargs))
            return self

        def srem(self, *args, **kwargs):
            self.commands.append(("srem", args, kwargs))
            return self

        def expire(self, *args, **kwargs):
            self.commands.append(("expire", args, kwargs))
            return self

        def delete(self, *args, **kwargs):
            self.commands.append(("delete", args, kwargs))
            return self

    monkeypatch.setattr(aioredis.Redis, "pipeline", MockPipeline)
    monkeypatch.setattr(syncredis.Redis, "pipeline", MockPipeline)