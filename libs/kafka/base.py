"""Reusable async Kafka producer/consumer wrappers (aiokafka).

Generic and reusable: both classes take a `KafkaSettings` value object
instead of importing any project's settings class, so they can be reused
as-is in another project.

Usage in a project's own main.py:

    from libs.kafka import KafkaSettings, Producer, Consumer

    kafka_settings = KafkaSettings(bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS)
    producer = Producer(kafka_settings)

    # in the FastAPI lifespan:
    await producer.connect()
    ...
    await producer.disconnect()

    # anywhere else:
    await producer.send("my-topic", b'{"event": "..."}')

Consuming (typically run as a separate worker task/process, not inside a
request handler):

    consumer = Consumer(kafka_settings, topics=["my-topic"], group_id="my-service")
    await consumer.connect()
    async for message in consumer.messages():
        ...
    await consumer.disconnect()
"""

from collections.abc import AsyncIterator
from dataclasses import dataclass, field

from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
from aiokafka.structs import ConsumerRecord


@dataclass(frozen=True)
class KafkaSettings:
    """Connection parameters for a Kafka cluster.

    A plain value object (not a pydantic BaseSettings) so libs/kafka has
    zero dependency on any particular settings/config library - the caller
    reads these values from wherever it likes and passes them in.
    """

    bootstrap_servers: str
    security_protocol: str = "PLAINTEXT"
    extra_config: dict = field(default_factory=dict)


class Producer:
    """Owns one AIOKafkaProducer.

    Mirrors the connect()/disconnect() shape used by libs/db and libs/redis
    for consistent app lifespan wiring.
    """

    def __init__(self, settings: KafkaSettings):
        """Store settings; the underlying producer isn't started until connect()."""
        self._settings = settings
        self._producer: AIOKafkaProducer | None = None

    async def connect(self) -> None:
        """Start the producer and its background connection to the cluster."""
        self._producer = AIOKafkaProducer(
            bootstrap_servers=self._settings.bootstrap_servers,
            security_protocol=self._settings.security_protocol,
            **self._settings.extra_config,
        )
        await self._producer.start()

    async def disconnect(self) -> None:
        """Flush and stop the producer (call this on app shutdown)."""
        if self._producer is not None:
            await self._producer.stop()

    async def send(self, topic: str, value: bytes, key: bytes | None = None) -> None:
        """Publish one message to `topic` and wait for the broker's ack.

        Args:
            topic: Kafka topic name.
            value: Raw message bytes (serialize your payload before calling this).
            key: Optional partition key.
        """
        if self._producer is None:
            raise RuntimeError("Producer.connect() must be called before send()")
        await self._producer.send_and_wait(topic, value=value, key=key)

    async def health_check(self) -> bool:
        """Return True if the producer's client reports at least one live broker connection."""
        if self._producer is None:
            return False
        try:
            return bool(self._producer.client.bootstrap_connected())
        except Exception:
            return False


class Consumer:
    """Owns one AIOKafkaConsumer for a fixed set of topics/group.

    Intended to be driven by a long-running worker task, not a request
    handler - iterate `messages()` in a background task started at app
    startup (or in a separate worker process for larger deployments).
    """

    def __init__(self, settings: KafkaSettings, topics: list[str], group_id: str):
        """Store settings; the underlying consumer isn't started until connect()."""
        self._settings = settings
        self._topics = topics
        self._group_id = group_id
        self._consumer: AIOKafkaConsumer | None = None

    async def connect(self) -> None:
        """Start the consumer and join the consumer group."""
        self._consumer = AIOKafkaConsumer(
            *self._topics,
            bootstrap_servers=self._settings.bootstrap_servers,
            security_protocol=self._settings.security_protocol,
            group_id=self._group_id,
            enable_auto_commit=True,
            **self._settings.extra_config,
        )
        await self._consumer.start()

    async def disconnect(self) -> None:
        """Leave the consumer group and stop the consumer (call this on app/worker shutdown)."""
        if self._consumer is not None:
            await self._consumer.stop()

    async def messages(self) -> AsyncIterator[ConsumerRecord]:
        """Async-iterate incoming messages until disconnect() is called."""
        if self._consumer is None:
            raise RuntimeError("Consumer.connect() must be called before messages()")
        async for message in self._consumer:
            yield message
