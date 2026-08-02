import json
from uuid import UUID
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from app.config import settings
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

def deserialize_from_json(data):
    try:
        return json.loads(data.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        raise ValueError(f"Data deserialization error: {e}")