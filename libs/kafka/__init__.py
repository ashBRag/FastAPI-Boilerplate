"""Async Kafka producer/consumer wrappers (aiokafka).

Self-contained: no dependency on any other libs/* package.
"""

from libs.kafka.base import Consumer, KafkaSettings, Producer

__all__ = ["Consumer", "KafkaSettings", "Producer"]
