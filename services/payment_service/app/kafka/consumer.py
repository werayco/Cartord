import asyncio
import json
import logging
from confluent_kafka import Consumer, Producer
from opentelemetry.trace import get_tracer_provider
from opentelemetry.instrumentation.confluent_kafka import ConfluentKafkaInstrumentor
from app.core.config import settings
from app.services.payment_processor import process_payment

logger = logging.getLogger(__name__)

class KafkaConsumer:
    def __init__(self):
        inst = ConfluentKafkaInstrumentor()
        tracer_provider = get_tracer_provider()

        consumer = Consumer({
            "bootstrap.servers": settings.KAFKA_BOOTSTRAP_SERVERS,
            "group.id": "payment-service",
            "auto.offset.reset": "earliest",
            "enable.auto.commit": False,
        })
        self.consumer = inst.instrument_consumer(consumer, tracer_provider=tracer_provider)

        dlq_producer = Producer({"bootstrap.servers": settings.KAFKA_BOOTSTRAP_SERVERS})
        self.dlq_producer = inst.instrument_producer(dlq_producer, tracer_provider)

        self._running = False

    @staticmethod
    def _event_type(msg):
        headers = msg.headers()
        if not headers:
            return None
        for k, v in headers:
            if k == "eventType":
                return v.decode() if isinstance(v, bytes) else v
        return None

    async def consume(self):
        self.consumer.subscribe(["order"])
        self._running = True
        loop = asyncio.get_event_loop()
        try:
            while self._running:
                msg = await loop.run_in_executor(None, self.consumer.poll, 1.0)
                if msg is None:
                    continue

                if msg.error():
                    logger.error(f"Kafka error: {msg.error()}")
                    continue

                key_bytes = msg.key()
                value_bytes = msg.value()
                event_type = self._event_type(msg)

                try:
                    value = json.loads(value_bytes.decode("utf-8")) if value_bytes else {}

                    if event_type == "order.created":
                        await process_payment(value)
                    else:
                        logger.info(f"Ignoring event type: {event_type}")

                    await loop.run_in_executor(None, self.consumer.commit, msg)
                except Exception as e:
                    logger.error(f"Failed to process message at offset {msg.offset()}: {e}")
                    await loop.run_in_executor(None, self._send_to_dlq, key_bytes, value_bytes, str(e))
                    await loop.run_in_executor(None, self.consumer.commit, msg)
        finally:
            self.consumer.close()

    def stop(self):
        self._running = False

    def _send_to_dlq(self, key_bytes, value_bytes, error: str):
        try:
            self.dlq_producer.produce(
                topic="order.dlq",
                key=key_bytes,
                value=json.dumps({
                    "original_value": value_bytes.decode(errors="replace") if value_bytes else None,
                    "error": error,
                }).encode(),
            )
            self.dlq_producer.flush()
        except Exception as dlq_err:
            logger.critical(f"Failed to publish to DLQ, message permanently lost: {dlq_err}")

kafka_manager = KafkaConsumer()