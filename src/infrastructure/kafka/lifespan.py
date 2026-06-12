"""Kafka startup and shutdown lifecycle hooks for FastAPI lifespan."""

import logging

from .consumer import start_consumers, stop_consumers
from .producer import start_producer, stop_producer

logger = logging.getLogger(__name__)


async def startup_kafka() -> None:
    """Start Kafka producer and all registered consumers.

    Hook into FastAPI lifespan:
        ```python
        from contextlib import asynccontextmanager
        from infrastructure.kafka.lifespan import startup_kafka, shutdown_kafka

        @asynccontextmanager
        async def lifespan(app: FastAPI):
            await startup_kafka()
            yield
            await shutdown_kafka()
        ```
    """
    logger.info("Starting Kafka...")
    await start_producer()
    await start_consumers()
    logger.info("Kafka startup complete.")


async def shutdown_kafka() -> None:
    """Stop all Kafka consumers and flush/stop the producer."""
    logger.info("Shutting down Kafka...")
    await stop_consumers()
    await stop_producer()
    logger.info("Kafka shutdown complete.")