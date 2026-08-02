from datetime import datetime, timedelta, timezone
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.config import settings
from app.db.session import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from jose import jwt, JWTError
from app.config import settings
import json
from app.schemas import Roles
import aiohttp


bearer_scheme = HTTPBearer()
async def get_current_user(access_token: HTTPAuthorizationCredentials = Depends(bearer_scheme)) -> dict:
    url = f"{settings.AUTH_BASE_URL}/api/v1/auth/user/me"
    headers = {"Authorization": f"Bearer {access_token.credentials}"}
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                response.raise_for_status()
                return await response.json()
    except aiohttp.ClientResponseError as e:
        raise HTTPException(status_code=e.status, detail=f"Failed to fetch user details: {e.message}")

async def update_inventory(sku: str, reserved_quantity: int) -> dict:
    url = f"{settings.INVENTORY_BASE_URL}/api/v1/inventory/reserved_inventory"
    headers = {"SHARED_API_KEY": settings.SERVICE_SHARED_KEY}

    async with aiohttp.ClientSession() as session:
        async with session.patch(url, data={"sku":sku, "reserved_quantity":reserved_quantity}, headers=headers) as response:
            response.raise_for_status()
            return await response.json()

def seralize_to_json(data):
    try:
        return json.dumps(data).encode("utf-8")
    except (TypeError, ValueError) as e:
        raise ValueError(f"Data serialization error: {e}")