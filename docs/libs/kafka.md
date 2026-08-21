# libs/kafka

Async Kafka producer/consumer wrappers (`aiokafka`), mirroring the
connect/disconnect shape used by `libs.db` and `libs.redis`.

## Setup - producer

```python
# app/main.py
from libs.kafka import KafkaSettings, Producer

kafka_settings = KafkaSettings(bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS)
producer = Producer(kafka_settings)

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        await producer.connect()
    except Exception as exc:
        logger.error("kafka_producer_connect_failed", error=str(exc))
    yield
    await producer.disconnect()
```

## Usage - publishing

```python
import json

async def publish_order_created(order: Order) -> None:
    payload = json.dumps({"order_id": order.id, "total": order.total}).encode()
    await producer.send("orders.created", value=payload, key=str(order.id).encode())
```

## Setup - consumer

Consumers are meant to run as a long-lived background task (or a separate
worker process), not inside a request handler:

```python
# app/workers/order_events.py
from libs.kafka import Consumer

consumer = Consumer(
    kafka_settings,
    topics=["orders.created"],
    group_id="my-service-order-events",
)

async def run() -> None:
    await consumer.connect()
    try:
        async for message in consumer.messages():
            payload = json.loads(message.value)
            await handle_order_created(payload)
    finally:
        await consumer.disconnect()
```

Start it as a background task at app startup:

```python
# app/main.py
import asyncio
from app.workers.order_events import run as run_order_events_worker

@asynccontextmanager
async def lifespan(app: FastAPI):
    await producer.connect()
    worker_task = asyncio.create_task(run_order_events_worker())
    yield
    worker_task.cancel()
    await producer.disconnect()
```

## Health check

```python
producer_healthy = await producer.health_check()  # never raises, returns True/False
```

## Notes

- `Producer.send()` waits for the broker's acknowledgment (`send_and_wait`) -
  it won't return until the message is confirmed written.
- `enable_auto_commit=True` is set on the consumer by default; pass extra
  `aiokafka` options via `KafkaSettings(extra_config={...})` if you need
  manual offset control or other tuning.
