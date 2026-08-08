import json
from collections.abc import Awaitable, Callable
from typing import Any
from app.db.redis_client import redis_client


async def idempotency(idempotency_key: str, user_id: str, operation: Callable[[], Awaitable[dict[str, Any]]], expires: int = 3600) -> dict[str, Any]:
    redis_key = f"idempotency:{user_id}:{idempotency_key}"
    claimed = await redis_client.set(redis_key, "PROCESSING", nx=True, ex=expires)

    if not claimed:
        existing_value = await redis_client.get(redis_key)

        if existing_value == "PROCESSING":
            return {"status": "processing", "message": "Request is already being processed."}

        return {"status": "completed", "result": json.loads(existing_value)}

    try:
        result = await operation()
        await redis_client.set(redis_key, json.dumps(result), ex=expires)
        return {"status": "completed", "result": result}

    except Exception:
        await redis_client.delete(redis_key)
        raise