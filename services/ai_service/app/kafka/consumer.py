import asyncio
import json
import logging
from datetime import datetime, timezone

from confluent_kafka import Consumer, Producer
from opentelemetry.trace import get_tracer_provider
from opentelemetry.instrumentation.confluent_kafka import ConfluentKafkaInstrumentor
from langchain_core.messages import HumanMessage

from app.core.config import settings
from app.core.utils import deserialize_from_json
from app.db.session import AsyncSessionLocal
from app.db.redis_client import redis_client
from app.models.message import Message
from app.nodes.entry_point import node_registry
from app.services.socket_registry import conversation_channel
from app.core.logging import logger

IDEMPOTENCY_TTL_SECONDS = 60 * 60

class KafkaConsumer:
    def __init__(self):
        inst = ConfluentKafkaInstrumentor()
        tracer_provider = get_tracer_provider()

        consumer = Consumer({
            "bootstrap.servers": settings.KAFKA_BOOTSTRAP_SERVERS,
            "group.id": "ai-service",
            "auto.offset.reset": "earliest",
            "enable.auto.commit": False,
        })
        self.consumer = inst.instrument_consumer(consumer, tracer_provider=tracer_provider)

        dlq_producer = Producer({"bootstrap.servers": settings.KAFKA_BOOTSTRAP_SERVERS})
        self.dlq_producer = inst.instrument_producer(dlq_producer, tracer_provider)

        self._running = False
        self._graph = None

    @staticmethod
    def _event_type(msg):
        headers = msg.headers()
        if not headers:
            return None
        for k, v in headers:
            if k == "eventType":
                return v.decode() if isinstance(v, bytes) else v
        return None

    async def get_graph(self):
        if self._graph is None:
            self._graph = await node_registry()
        return self._graph

    async def consume(self):
        self.consumer.subscribe(["chat"])
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

                event_type = self._event_type(msg)
                if event_type != "message.created":
                    await loop.run_in_executor(None, self.consumer.commit, msg)
                    continue

                key_bytes = msg.key()
                value_bytes = msg.value()

                try:
                    payload = deserialize_from_json(value_bytes)
                    await self.handle_message_created(payload)
                    await loop.run_in_executor(None, self.consumer.commit, msg)
                except Exception as e:
                    logger.error(f"Failed to process message at offset {msg.offset()}: {e}")
                    await loop.run_in_executor(None, self._send_to_dlq, key_bytes, value_bytes, str(e))
                    await loop.run_in_executor(None, self.consumer.commit, msg)
        finally:
            self.consumer.close()

    async def handle_message_created(self, payload: dict) -> None:
        message_id = payload["message_id"]
        conversation_id = payload["conversation_id"]
        content = payload["content"]
        user_id = payload.get("user_id")
        access_token = payload.get("access_token")
        is_admin = payload.get("is_admin", False)

        dedup_key = f"processed:{message_id}"
        was_new = await redis_client.set(dedup_key, "1", nx=True, ex=IDEMPOTENCY_TTL_SECONDS)
        if not was_new:
            logger.info(f"Message {message_id} already processed, skipping redelivery")
            return

        channel = conversation_channel(conversation_id)
        graph = await self.get_graph()
        config = {"configurable": {"thread_id": conversation_id}}
        inputs = {
            "messages": [HumanMessage(content=content)],
            "user_id": user_id,
            "access_token": access_token,
            "is_admin": is_admin,
        }

        full_reply = ""
        try:
            async for event in graph.astream_events(inputs, version="v2", config=config):
                if event["event"] != "on_chat_model_stream":
                    continue
                chunk = event["data"].get("chunk")
                delta = getattr(chunk, "content", None) if chunk else None
                if not delta:
                    continue
                full_reply += delta
                await redis_client.publish(channel, json.dumps({
                    "type": "token",
                    "conversation_id": conversation_id,
                    "reply_to_message_id": message_id,
                    "delta": delta,
                }))
        except Exception:
            await redis_client.publish(channel, json.dumps({
                "type": "error",
                "conversation_id": conversation_id,
                "reply_to_message_id": message_id,
                "error": "Something went wrong generating a reply, try again.",
            }))
            raise

        assistant_message_id = await self.persist_reply(conversation_id, full_reply)

        await redis_client.publish(channel, json.dumps({
            "type": "done",
            "conversation_id": conversation_id,
            "reply_to_message_id": message_id,
            "message_id": assistant_message_id,
        }))

    @staticmethod
    async def persist_reply(conversation_id: str, content: str) -> str:
        async with AsyncSessionLocal() as db:
            message = Message(
                conversation_id=conversation_id,
                role="assistant",
                content=content,
                created_at=datetime.now(timezone.utc),
            )
            db.add(message)
            await db.commit()
            await db.refresh(message)
            return str(message.id)

    def stop(self):
        self._running = False

    def _send_to_dlq(self, key_bytes, value_bytes, error: str):
        try:
            self.dlq_producer.produce(
                topic="chat.dlq",
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