from fastapi import WebSocket, HTTPException
from app.core.config import settings
from app.core.logging import logger
import aiohttp
import json

async def authenticate(websocket: WebSocket) -> str:
    token = websocket.query_params.get("token")
    if not token:
        raise ValueError("Missing authentication token")    
    return token

async def get_current_buyer(websocket: WebSocket) -> dict:
    url = f"{settings.AUTH_BASE_URL}/api/v1/auth/buyer/me"
    access_token = await authenticate(websocket)
    headers = {"Authorization": f"Bearer {access_token}"}    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                response.raise_for_status()
                return await response.json()
    except aiohttp.ClientResponseError as e:
        logger.error(f"Auth service error: {e.status} - {e.message}")
        raise HTTPException(status_code=e.status, detail=f"Failed to fetch user details: {e.message}")
    except aiohttp.ClientError as e:
        logger.error(f"Connection error: {e}")
        raise HTTPException(status_code=503, detail="Authentication service unavailable")

async def get_current_seller(websocket: WebSocket) -> dict:
    url = f"{settings.AUTH_BASE_URL}/api/v1/auth/seller/me"
    access_token = await authenticate(websocket)
    headers = {"Authorization": f"Bearer {access_token}"}
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                response.raise_for_status()
                data = await response.json()
                logger.info(f"Buyer authenticated: {data.get('id')}")
                return data
    except aiohttp.ClientResponseError as e:
        logger.error(f"Auth service error: {e.status} - {e.message}")
        raise HTTPException(status_code=e.status, detail=f"Failed to fetch user details: {e.message}")
    except aiohttp.ClientError as e:
        logger.error(f"Connection error: {e}")
        raise HTTPException(status_code=503, detail="Authentication service unavailable")

def deserialize_from_json(data):
    try:
        return json.loads(data.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        raise ValueError(f"Data deserialization error: {e}")