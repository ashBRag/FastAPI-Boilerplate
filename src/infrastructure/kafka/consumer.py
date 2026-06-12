import asyncio
import json
import logging
from collections.abc import Callable
from typing import Any

from aiokafka import AIOKafkaConsumer, ConsumerRecord

from ..config.settings import settings

logger = logging.getLogger(__name__)

# Registry of all @kafka_consumer decorated handlers
# { topic: [(group_id, handler_fn), ...] }
_consumer_registry: dict[str, list[tuple[str, Callable]]] = {}
_running_tasks: list[asyncio.Task] = []


def kafka_consumer(
    topic: str,
    group_id: str | None = None,
) -> Callable:
    """Decorator to register an async function as a Kafka consumer handler.

    The decorated function is registered at import time and started
    during FastAPI lifespan via start_consumers().

    Args:
        topic: Kafka topic to consume from.
        group_id: Consumer group ID. Defaults to KAFKA_CONSUMER_GROUP_ID from settings.

    Usage:
        ```python
        from infrastructure.kafka.consumer import kafka_consumer

        @kafka_consumer(topic="orders")
        async def handle_order(message: dict) -> None:
            print(f"Received order: {message}")

        @kafka_consumer(topic="payments", group_id="payments-group")
        async def handle_payment(message: dict) -> None:
            print(f"Received payment: {message}")
        ```

    Note:
        Handlers receive the deserialized message value as a dict.
        For raw ConsumerRecord access, annotate the argument as ConsumerRecord.
    """
    def decorator(fn: Callable) -> Callable:
        resolved_group = group_id or settings.KAFKA_CONSUMER_GROUP_ID
        if topic not in _consumer_registry:
            _consumer_registry[topic] = []
        _consumer_registry[topic].append((resolved_group, fn))
        logger.debug(f"Registered Kafka consumer: topic={topic} group={resolved_group} fn={fn.__name__}")
        return fn

    return decorator


def _build_consumer(topic: str, group_id: str) -> AIOKafkaConsumer:
    """Build AIOKafkaConsumer for a given topic and group."""
    kwargs: dict[str, Any] = dict(
        topic,
        bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS_LIST,
        client_id=f"{settings.KAFKA_CLIENT_ID}-consumer",
        group_id=group_id,
        auto_offset_reset=settings.KAFKA_CONSUMER_AUTO_OFFSET_RESET,
        enable_auto_commit=settings.KAFKA_CONSUMER_ENABLE_AUTO_COMMIT,
        max_poll_records=settings.KAFKA_CONSUMER_MAX_POLL_RECORDS,
        session_timeout_ms=settings.KAFKA_CONSUMER_SESSION_TIMEOUT_MS,
        value_deserializer=lambda v: json.loads(v.decode("utf-8")),
    )

    if settings.KAFKA_SECURITY_PROTOCOL != "PLAINTEXT":
        kwargs["security_protocol"] = settings.KAFKA_SECURITY_PROTOCOL
        if settings.KAFKA_SASL_MECHANISM:
            kwargs["sasl_mechanism"] = settings.KAFKA_SASL_MECHANISM
            kwargs["sasl_plain_username"] = settings.KAFKA_SASL_USERNAME
            kwargs["sasl_plain_password"] = settings.KAFKA_SASL_PASSWORD

    return AIOKafkaConsumer(**kwargs)


async def _consume_loop(topic: str, group_id: str, handler: Callable) -> None:
    """Long-running consume loop for a single topic/handler pair."""
    consumer = _build_consumer(topic, group_id)
    await consumer.start()
    logger.info(f"Kafka consumer started: topic={topic} group={group_id}")

    try:
        async for msg in consumer:
            try:
                await handler(msg.value)
                if not settings.KAFKA_CONSUMER_ENABLE_AUTO_COMMIT:
                    await consumer.commit()
            except Exception:
                logger.exception(
                    f"Error in Kafka handler: topic={topic} "
                    f"partition={msg.partition} offset={msg.offset}"
                )
    finally:
        await consumer.stop()
        logger.info(f"Kafka consumer stopped: topic={topic} group={group_id}")


async def start_consumers() -> None:
    """Start all registered @kafka_consumer handlers as asyncio tasks.

    Called during FastAPI lifespan startup.
    """
    if not settings.KAFKA_ENABLED:
        logger.info("Kafka is disabled. Skipping consumer startup.")
        return

    for topic, handlers in _consumer_registry.items():
        for group_id, handler in handlers:
            task = asyncio.create_task(
                _consume_loop(topic, group_id, handler),
                name=f"kafka-consumer-{topic}-{handler.__name__}",
            )
            _running_tasks.append(task)

    logger.info(f"Started {len(_running_tasks)} Kafka consumer task(s).")


async def stop_consumers() -> None:
    """Cancel all running consumer tasks.

    Called during FastAPI lifespan shutdown.
    """
    for task in _running_tasks:
        task.cancel()

    if _running_tasks:
        await asyncio.gather(*_running_tasks, return_exceptions=True)
        _running_tasks.clear()
        logger.info("All Kafka consumer tasks stopped.")