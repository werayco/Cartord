from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.config import settings
import json
import aiohttp
from jose import jwt, JWTError
from app.services.circuit_breaker import breaker as inventory_breaker

bearer_scheme = HTTPBearer()

async def get_current_user(token: HTTPAuthorizationCredentials = Depends(bearer_scheme)) -> dict:
    credentials_exception = HTTPException(status_code=401, detail="Invalid or expired token")
    try:
        payload = jwt.decode(token.credentials, settings.JWT_PUBLIC_KEY, algorithms=["RS256"])
        if payload.get("type") != "access":
            raise credentials_exception
        return {"id": payload["sub"], "email": payload.get("email"), "role": payload.get("role")}
    except (JWTError, KeyError):
        raise credentials_exception
    
# async def get_current_user(token: HTTPAuthorizationCredentials = Depends(bearer_scheme)) -> dict:
#     credentials_exception = HTTPException(status_code=401, detail="Invalid or expired token")
#     try:
#         payload = jwt.decode(token.credentials, settings.SECRET_KEY, algorithms=["HS256"])
#         if payload.get("type") != "access":
#             raise credentials_exception
#         return payload
#     except (JWTError, KeyError):
#         raise credentials_exception
    
# @inventory_breaker
async def update_inventory(sku: str, reserved_quantity: int) -> dict:
    url = f"{settings.INVENTORY_BASE_URL}/inventory/reserve"
    headers = {"SHARED_API_KEY": settings.SERVICE_SHARED_KEY}
    print(f"request header is: {headers}")

    async with aiohttp.ClientSession() as session:
        print("sending request...")
        async with session.patch(url, json={"sku":sku, "reserved_quantity":reserved_quantity}, headers=headers) as response:
            response.raise_for_status()
            response_json = await response.json()
            print(f"response from inventory reservsation is {response_json}")
            return response_json

def seralize_to_json(data):
    try:
        return json.dumps(data).encode("utf-8")
    except (TypeError, ValueError) as e:
        raise ValueError(f"Data serialization error: {e}")