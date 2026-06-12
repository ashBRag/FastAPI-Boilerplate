import json
import logging
from collections.abc import AsyncGenerator
from typing import Any

from aiokafka import AIOKafkaProducer

from ..config.settings import settings

logger = logging.getLogger(__name__)

_producer: AIOKafkaProducer | None = None


def _build_producer() -> AIOKafkaProducer:
    """Build AIOKafkaProducer from settings."""
    kwargs: dict[str, Any] = dict(
        bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS_LIST,
        client_id=settings.KAFKA_CLIENT_ID,
        acks=settings.KAFKA_PRODUCER_ACKS,
        max_batch_size=settings.KAFKA_PRODUCER_MAX_BATCH_SIZE,
        linger_ms=settings.KAFKA_PRODUCER_LINGER_MS,
        request_timeout_ms=settings.KAFKA_PRODUCER_REQUEST_TIMEOUT_MS,
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
        key_serializer=lambda k: k.encode("utf-8") if isinstance(k, str) else k,
    )

    if settings.KAFKA_SECURITY_PROTOCOL != "PLAINTEXT":
        kwargs["security_protocol"] = settings.KAFKA_SECURITY_PROTOCOL
        if settings.KAFKA_SASL_MECHANISM:
            kwargs["sasl_mechanism"] = settings.KAFKA_SASL_MECHANISM
            kwargs["sasl_plain_username"] = settings.KAFKA_SASL_USERNAME
            kwargs["sasl_plain_password"] = settings.KAFKA_SASL_PASSWORD

    return AIOKafkaProducer(**kwargs)


async def start_producer() -> None:
    """Initialize and start the shared Kafka producer.

    Called during FastAPI lifespan startup.

    Raises:
        RuntimeError: If Kafka is not enabled in settings.
    """
    global _producer

    if not settings.KAFKA_ENABLED:
        logger.info("Kafka is disabled. Skipping producer startup.")
        return

    if _producer is None:
        _producer = _build_producer()

    await _producer.start()
    logger.info("Kafka producer started.")


async def stop_producer() -> None:
    """Stop and flush the shared Kafka producer.

    Called during FastAPI lifespan shutdown.
    """
    global _producer

    if _producer is not None:
        await _producer.stop()
        _producer = None
        logger.info("Kafka producer stopped.")


async def get_kafka_producer() -> AsyncGenerator[AIOKafkaProducer, None]:
    """FastAPI dependency that yields the shared Kafka producer.

    Usage:
        ```python
        from fastapi import Depends
        from aiokafka import AIOKafkaProducer

        @router.post("/orders")
        async def create_order(producer: AIOKafkaProducer = Depends(get_kafka_producer)):
            await producer.send("orders", value={"id": "123"}, key="order-123")
        ```

    Yields:
        AIOKafkaProducer: The shared producer instance.

    Raises:
        RuntimeError: If Kafka is disabled or producer is not started.
    """
    if not settings.KAFKA_ENABLED:
        raise RuntimeError("Kafka is not enabled. Set KAFKA_ENABLED=true in your environment.")

    if _producer is None:
        raise RuntimeError("Kafka producer is not started. Ensure lifespan startup ran.")

    yield _producer