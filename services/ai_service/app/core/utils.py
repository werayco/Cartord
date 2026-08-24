import logging
import uuid
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from pydantic import ValidationError
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.config import settings
import aiohttp

bearer_scheme = HTTPBearer()
async def authenticate(websocket: WebSocket) -> uuid.UUID:
    token = websocket.query_params.get("token")
    if not token:
        raise ValueError("missing auth token")
    try:
        return uuid.UUID(token)
    except ValueError:
        raise ValueError("invalid auth token") from None


async def get_current_user(access_token: HTTPAuthorizationCredentials = Depends(bearer_scheme)) -> dict:
    url = f"{settings.AUTH_BASE_URL}/api/v1/auth/employee/me"
    headers = {"Authorization": f"Bearer {access_token.credentials}"}
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                response.raise_for_status()
                return await response.json()
    except aiohttp.ClientResponseError as e:
        raise HTTPException(status_code=e.status, detail=f"Failed to fetch user details: {e.message}")
