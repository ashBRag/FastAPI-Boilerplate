from pydantic_settings import BaseSettings

from ..config.settings import config


class KafkaSettings(BaseSettings):
    """Kafka connection and behavior settings."""

    KAFKA_ENABLED: bool = config("KAFKA_ENABLED", default=False, cast=bool)

    KAFKA_BOOTSTRAP_SERVERS: str = config("KAFKA_BOOTSTRAP_SERVERS", default="localhost:9092")
    KAFKA_CLIENT_ID: str = config("KAFKA_CLIENT_ID", default="fastapi-app")

    # Producer
    KAFKA_PRODUCER_ACKS: str = config("KAFKA_PRODUCER_ACKS", default="all")
    KAFKA_PRODUCER_MAX_BATCH_SIZE: int = config("KAFKA_PRODUCER_MAX_BATCH_SIZE", default=16384, cast=int)
    KAFKA_PRODUCER_LINGER_MS: int = config("KAFKA_PRODUCER_LINGER_MS", default=0, cast=int)
    KAFKA_PRODUCER_REQUEST_TIMEOUT_MS: int = config("KAFKA_PRODUCER_REQUEST_TIMEOUT_MS", default=30000, cast=int)

    # Consumer
    KAFKA_CONSUMER_GROUP_ID: str = config("KAFKA_CONSUMER_GROUP_ID", default="fastapi-consumer-group")
    KAFKA_CONSUMER_AUTO_OFFSET_RESET: str = config("KAFKA_CONSUMER_AUTO_OFFSET_RESET", default="earliest")
    KAFKA_CONSUMER_ENABLE_AUTO_COMMIT: bool = config("KAFKA_CONSUMER_ENABLE_AUTO_COMMIT", default=False, cast=bool)
    KAFKA_CONSUMER_MAX_POLL_RECORDS: int = config("KAFKA_CONSUMER_MAX_POLL_RECORDS", default=500, cast=int)
    KAFKA_CONSUMER_SESSION_TIMEOUT_MS: int = config("KAFKA_CONSUMER_SESSION_TIMEOUT_MS", default=30000, cast=int)

    # Security (optional)
    KAFKA_SECURITY_PROTOCOL: str = config("KAFKA_SECURITY_PROTOCOL", default="PLAINTEXT")
    KAFKA_SASL_MECHANISM: str | None = config("KAFKA_SASL_MECHANISM", default=None)
    KAFKA_SASL_USERNAME: str | None = config("KAFKA_SASL_USERNAME", default=None)
    KAFKA_SASL_PASSWORD: str | None = config("KAFKA_SASL_PASSWORD", default=None)

    @property
    def KAFKA_BOOTSTRAP_SERVERS_LIST(self) -> list[str]:
        """Split comma-separated bootstrap servers into a list."""
        return [s.strip() for s in self.KAFKA_BOOTSTRAP_SERVERS.split(",")]