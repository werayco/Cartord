from app.config import settings
from confluent_kafka import Producer

class KafkaManager:
    def __init__(self):
        self.producer = Producer({
            'bootstrap.servers': settings.KAFKA_BOOTSTRAP_SERVERS,
            'client.id': settings.KAFKA_CLIENT_ID
        })

    def produce(self, topic: str, key: str, value: str):
        self.producer.produce(topic=topic, key=key, value=value)
        self.producer.flush()

kafka_manager = KafkaManager()