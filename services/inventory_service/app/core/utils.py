from datetime import datetime, timedelta, timezone
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.config import settings
from app.core.schemas import Roles
from jose import jwt, JWTError
import json
from app.core.schemas import Roles
import redis
import aiohttp

bearer_scheme = HTTPBearer()

def to_json_safe(data: dict) -> dict:
    return json.loads(json.dumps(data, default=str))

async def get_current_user(token: HTTPAuthorizationCredentials = Depends(bearer_scheme)) -> dict:
    credentials_exception = HTTPException(status_code=401, detail="Invalid or expired token")
    try:
        payload = jwt.decode(token.credentials, settings.JWT_PRIVATE_KEY, algorithms=["HS256"])
        if payload.get("type") != "access":
            raise credentials_exception
        return {"id": payload["sub"], "email": payload.get("email"), "role": payload.get("role")}
    except (JWTError, KeyError):
        raise credentials_exception

async def get_admin_user(current_user: dict = Depends(get_current_user)) -> dict:
    if current_user.get("role") != Roles.ADMIN.value:
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user
    
def seralize_to_json(data):
    try:
        return json.dumps(data).encode("utf-8")
    except (TypeError, ValueError) as e:
        raise ValueError(f"Data serialization error: {e}")
