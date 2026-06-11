from pydantic_settings import BaseSettings

from ....config.settings import config


class MySQLSettings(BaseSettings):
    """MySQL connection settings."""

    MYSQL_ENABLED: bool = config("MYSQL_ENABLED", default=False, cast=bool)
    MYSQL_USER: str = config("MYSQL_USER", default="mysql")
    MYSQL_PASSWORD: str = config("MYSQL_PASSWORD", default="mysql")
    MYSQL_SERVER: str = config("MYSQL_SERVER", default="localhost")
    MYSQL_PORT: int = config("MYSQL_PORT", default=3306, cast=int)
    MYSQL_DB: str = config("MYSQL_DB", default="app")
    MYSQL_ASYNC_PREFIX: str = config("MYSQL_ASYNC_PREFIX", default="mysql+aiomysql://")
    MYSQL_SYNC_PREFIX: str = config("MYSQL_SYNC_PREFIX", default="mysql+pymysql://")

    MYSQL_POOL_SIZE: int = config("MYSQL_POOL_SIZE", default=20, cast=int)
    MYSQL_MAX_OVERFLOW: int = config("MYSQL_MAX_OVERFLOW", default=0, cast=int)
    MYSQL_CONNECT_TIMEOUT: int = config("MYSQL_CONNECT_TIMEOUT", default=10, cast=int)

    @property
    def MYSQL_URL(self) -> str:
        """Get the full async MySQL URL.

        Checks for MYSQL_URL environment variable first (production pattern),
        then falls back to constructing from individual components.
        """
        direct_url = config("MYSQL_URL", default=None)
        if direct_url:
            return direct_url

        return (
            f"{self.MYSQL_ASYNC_PREFIX}{self.MYSQL_USER}:"
            f"{self.MYSQL_PASSWORD}@{self.MYSQL_SERVER}:"
            f"{self.MYSQL_PORT}/{self.MYSQL_DB}"
        )