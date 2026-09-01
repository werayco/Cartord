from datetime import datetime, timedelta, timezone
from uuid import UUID
import bcrypt
from jose import jwt, JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.config import settings
from app.models.seller import Seller
from app.db.session import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from jose import jwt, JWTError
import secrets
import hashlib
from app.db.redis_client import redis_client
from app.services.circuit_breaker import breaker as payment_breaker
import aiohttp
bearer_scheme = HTTPBearer()

ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES
REFRESH_TOKEN_EXPIRE_DAYS = settings.REFRESH_TOKEN_EXPIRE_DAYS

@payment_breaker 
async def create_wallet(customer_id: UUID) -> dict:
    url = f"{settings.PAYMENT_BASE_URL}/payment/wallet"
    headers = {"SHARED_API_KEY": settings.SERVICE_SHARED_KEY,"Content-Type": "application/json"}

    async with aiohttp.ClientSession() as session:
        async with session.post(url, json={"customer_id": str(customer_id)},headers=headers) as response:
            response.raise_for_status()
            return await response.json()
        
def get_current_user_dep(table_name):
    async def _get_current_user(
        token: HTTPAuthorizationCredentials = Depends(bearer_scheme),
        db: AsyncSession = Depends(get_db),
    ):
        credentials_exception = HTTPException(status_code=401, detail="Invalid or expired token")
        try:
            payload = jwt.decode(token.credentials, settings.JWT_PUBLIC_KEY, algorithms=["RS256"])
            if payload.get("type") != "access":
                raise credentials_exception
            user_id = UUID(payload["sub"])
        except (JWTError, ValueError, KeyError):
            raise credentials_exception
        result = await db.execute(select(table_name).where(table_name.id == user_id))
        user = result.scalar_one_or_none()
        if user is None:
            raise credentials_exception
        return user
    return _get_current_user

def _build_token(user, token_type: str, expires_delta: timedelta) -> str:
    now = datetime.now(timezone.utc)
    role = getattr(user, "role", None)
    payload = {
        "sub": str(user.id),
        "email": user.email,
        "role": role.value if role is not None else "buyer",
        "iat": now,
        "exp": now + expires_delta,
        "type": token_type,
    }
    return jwt.encode(payload, settings.JWT_PRIVATE_KEY, algorithm="RS256")

async def issue_access_token(user) -> str:
    return _build_token(user, "access", timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))

async def get_tokens(user):
    access = await issue_access_token(user)          # now takes the full user object, not just .id
    refresh = await issue_refresh_token()
    redis_client.set(f"refresh:{user.id}", hash_token(refresh), ex=REFRESH_TOKEN_EXPIRE_DAYS * 86400)
    return {"access_token": access, "refresh_token": refresh}

async def get_tokens(user_id):
    access = await issue_access_token(user_id.id)
    refresh = await issue_refresh_token()
    redis_client.set(f"refresh:{user_id.id}", hash_token(refresh), ex=REFRESH_TOKEN_EXPIRE_DAYS * 86400)
    return {"access_token": access, "refresh_token": refresh}

async def issue_refresh_token() -> str:
    return secrets.token_urlsafe(64)

def hash_password(password: str) -> str:
    password_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')

def verify_password(password: str, hashed_password: str) -> bool:
    password_bytes = password.encode('utf-8')
    hashed_bytes = hashed_password.encode('utf-8')    
    return bcrypt.checkpw(password_bytes, hashed_bytes)

def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()

async def cache_refresh_tokens(user_id: UUID, refresh_token: str, user):  # pass the loaded row in from the router

    key = f"refresh:{user_id}"
    stored_hash = redis_client.get(key)

    if not stored_hash:
        raise Exception("Refresh token has expired")

    if stored_hash != hash_token(refresh_token):
        raise Exception("Invalid refresh token")

    new_access_token = await issue_access_token(user)
    new_refresh_token = await issue_refresh_token()

    redis_client.set(
        key,
        hash_token(new_refresh_token),
        ex=REFRESH_TOKEN_EXPIRE_DAYS * 86400,
    )

    return {
        "access_token": new_access_token,
        "refresh_token": new_refresh_token,
    }