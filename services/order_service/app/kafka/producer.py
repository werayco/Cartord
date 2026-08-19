from opentelemetry.trace import get_tracer_provider
from opentelemetry.instrumentation.confluent_kafka import ConfluentKafkaInstrumentor
from app.core.config import settings
from confluent_kafka import Producer

class KafkaManager:
    def __init__(self):
        producer = Producer({
            'bootstrap.servers': settings.KAFKA_BOOTSTRAP_SERVERS,
            'client.id': settings.KAFKA_CLIENT_ID
        })
        self.producer = ConfluentKafkaInstrumentor().instrument_producer(
            producer, get_tracer_provider()
        )

    def produce(self, topic: str, key: str, value: str):
        self.producer.produce(topic=topic, key=key, value=value)
        self.producer.flush()


kafka_manager = KafkaManager()