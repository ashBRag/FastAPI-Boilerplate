import logging
import os

from starlette.config import Config

from ..aws.config import AWSSettings
from ..cache.config import CacheSettings
from ..database.mongodb.config import MongoDBSettings
from ..database.mysql.config import MySQLSettings
from ..database.postgresql.config import PostgreSQLSettings
from ..kafka.config import KafkaSettings
from ..rate_limit.config import RateLimiterSettings
from ..taskiq.config import TaskiqSettings
from ..vault.config import VaultSettings
from .base import (
    AdminSettings,
    APIDocSettings,
    APISettings,
    AppSettings,
    AuthSettings,
    CompressionSettings,
    CORSSettings,
    EnvironmentSettings,
    LoggingSettings,
    SecuritySettings,
    SQLAdminSettings,
)

logger = logging.getLogger(__name__)

current_file_dir = os.path.dirname(os.path.realpath(__file__))
project_root = os.path.abspath(os.path.join(current_file_dir, "..", "..", "..", ".."))

env_paths = [
    "/app/.env",
    os.path.join(project_root, ".env"),
    "/.env",
]

env_path = next((path for path in env_paths if os.path.isfile(path)), env_paths[0])
logger.info(f"Using environment file at: {env_path}")

config = Config(env_path)


class Settings(
    # App
    EnvironmentSettings,
    AppSettings,
    APISettings,
    APIDocSettings,
    AuthSettings,
    AdminSettings,
    SQLAdminSettings,
    SecuritySettings,
    LoggingSettings,
    CORSSettings,
    CompressionSettings,
    # Infrastructure
    AWSSettings,
    PostgreSQLSettings,
    MySQLSettings,
    MongoDBSettings,
    CacheSettings,
    RateLimiterSettings,
    TaskiqSettings,
    KafkaSettings,
    VaultSettings
):
    """Assembled settings — imports only, no field definitions here."""
    pass


settings = Settings()


def get_settings() -> Settings:
    return settings