from datetime import datetime, timedelta, timezone
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.config import settings
from app.db.session import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from jose import jwt, JWTError
from app.core.config import settings
import json
from app.core.schemas import Roles
import redis
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

async def get_redis_client():
    redis_client = redis.Redis(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        decode_responses=True,
    )
    return redis_client

def seralize_to_json(data):
    try:
        return json.dumps(data).encode("utf-8")
    except (TypeError, ValueError) as e:
        raise ValueError(f"Data serialization error: {e}")
    

def get_current_user_dep(table_name):
    async def _get_current_user(
        token: HTTPAuthorizationCredentials = Depends(bearer_scheme),
        db: AsyncSession = Depends(get_db),
    ):
        credentials_exception = HTTPException(status_code=401, detail="Invalid or expired token")
        permission_exception = HTTPException(status_code=403, detail="You aren't permitted to use this endpoint")
        try:
            payload = jwt.decode(token.credentials, settings.SECRET_KEY, algorithms=["HS256"])
            if payload.get("type") != "access":
                raise credentials_exception
            if payload.get("role") == Roles.EMPLOYEE:
                raise permission_exception
            user_id = UUID(payload["sub"])
        except (JWTError, ValueError, KeyError):
            raise credentials_exception
        result = await db.execute(select(table_name).where(table_name.id == user_id))
        user = result.scalar_one_or_none()
        if user is None:
            raise credentials_exception
        return user
    return _get_current_user