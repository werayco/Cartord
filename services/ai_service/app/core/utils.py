from fastapi import WebSocket, HTTPException, Depends
from app.core.config import settings
from app.core.logging import logger
import json
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.schemas import Roles
from jose import jwt, JWTError

async def authenticate(websocket: WebSocket) -> str:
    token = websocket.query_params.get("token")
    if not token:
        raise ValueError("Missing authentication token")    
    return token

bearer_scheme = HTTPBearer()

async def get_current_user(websocket: WebSocket) -> dict:
    token = websocket.query_params.get("token")
    if not token:
        raise HTTPException(status_code=401, detail="Missing authentication token")
    try:
        payload = jwt.decode(token, settings.JWT_PRIVATE_KEY, algorithms=["HS256"])
        if payload.get("type") != "access":
            raise HTTPException(status_code=401, detail="Invalid or expired token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return {
        "id": payload["sub"],
        "email": payload.get("email"),
        "role": payload.get("role"),
        "is_admin": payload.get("role") == Roles.ADMIN.value,
    }
    
async def get_admin(token: HTTPAuthorizationCredentials = Depends(bearer_scheme)) -> dict:
    user = await get_current_user(token)
    if user["role"] != Roles.ADMIN.value:
        raise HTTPException(status_code=403, detail="Admin access required")
    return user

def deserialize_from_json(data):
    try:
        return json.loads(data.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        raise ValueError(f"Data deserialization error: {e}")