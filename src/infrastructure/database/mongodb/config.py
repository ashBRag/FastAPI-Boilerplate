from pydantic_settings import BaseSettings
from starlette.config import Config

from ....config.settings import config


class MongoDBSettings(BaseSettings):
    """MongoDB connection settings."""

    MONGODB_ENABLED: bool = config("MONGODB_ENABLED", default=False, cast=bool)
    MONGODB_URI: str = config("MONGODB_URI", default="mongodb://localhost:27017")
    MONGODB_DB: str = config("MONGODB_DB", default="app")
    MONGODB_MAX_POOL_SIZE: int = config("MONGODB_MAX_POOL_SIZE", default=10, cast=int)
    MONGODB_MIN_POOL_SIZE: int = config("MONGODB_MIN_POOL_SIZE", default=1, cast=int)
    MONGODB_CONNECT_TIMEOUT_MS: int = config("MONGODB_CONNECT_TIMEOUT_MS", default=5000, cast=int)
    MONGODB_SERVER_SELECTION_TIMEOUT_MS: int = config("MONGODB_SERVER_SELECTION_TIMEOUT_MS", default=5000, cast=int)