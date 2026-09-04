import json

from fastapi import Depends, HTTPException
from fastapi.params import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import jwt, JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings

bearer_scheme = HTTPBearer()

async def get_current_user(token: HTTPAuthorizationCredentials = Depends(bearer_scheme)) -> dict:
    credentials_exception = HTTPException(status_code=401, detail="Invalid or expired token")
    try:
        payload = jwt.decode(token.credentials, settings.JWT_PRIVATE_KEY, algorithms=["HS256"])
        if payload.get("type") != "access":
            raise credentials_exception
        return {"id": payload["sub"], "email": payload.get("email"), "role": payload.get("role")}
    except (JWTError, KeyError):
        raise credentials_exception
    
def seralize_to_json(data):
    try:
        return json.dumps(data).encode("utf-8")
    except (TypeError, ValueError) as e:
        raise ValueError(f"Data serialization error: {e}")