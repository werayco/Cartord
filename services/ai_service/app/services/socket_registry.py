import asyncio
import logging
from fastapi import WebSocket
from app.db.redis_client import redis_client
from app.core.logging import logger

def conversation_channel(conversation_id: str) -> str:
    return f"conv:{conversation_id}"

class ConversationBridge:
    def __init__(self, websocket: WebSocket):
        self._websocket = websocket
        self._tasks: dict[str, asyncio.Task] = {}

    async def ensure_subscribed(self, conversation_id: str) -> None:
        if conversation_id in self._tasks:
            return
        self._tasks[conversation_id] = asyncio.create_task(
            self._listen(conversation_id)
        )

    async def _listen(self, conversation_id: str) -> None:
        channel = conversation_channel(conversation_id)
        pubsub = redis_client.pubsub()
        try:
            await pubsub.subscribe(channel)
            logger.info(f"Subscribed to {channel}")
            async for message in pubsub.listen():
                if message["type"] != "message":
                    continue
                await self._websocket.send_text(message["data"])
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Redis listener error for {channel}: {e}")
        finally:
            try:
                await pubsub.unsubscribe(channel)
                await pubsub.close()
            except Exception:
                pass
            logger.info(f"Unsubscribed from {channel}")

    async def close(self) -> None:
        for task in self._tasks.values():
            task.cancel()
        for task in self._tasks.values():
            try:
                await task
            except asyncio.CancelledError:
                pass
        self._tasks.clear()