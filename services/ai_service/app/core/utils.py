import json

from fastapi import Depends, HTTPException, WebSocket
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from app.core.config import settings
from app.core.schemas import Roles


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


async def get_user(
    token: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> dict:
    credentials_exception = HTTPException(
        status_code=401, detail="Invalid or expired token"
    )
    try:
        payload = jwt.decode(
            token.credentials, settings.JWT_PRIVATE_KEY, algorithms=["HS256"]
        )
        if payload.get("type") != "access":
            raise credentials_exception
        return {
            "id": payload["sub"],
            "email": payload.get("email"),
            "role": payload.get("role"),
        }
    except (JWTError, KeyError):
        raise credentials_exception


async def get_admin(
    token: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> dict:
    user = await get_user(token)
    if user["role"] != Roles.ADMIN.value:
        raise HTTPException(status_code=403, detail="Admin access required")
    return user


def deserialize_from_json(data):
    try:
        return json.loads(data.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        raise ValueError(f"Data deserialization error: {e}")


def _price(value) -> float:
    return float(value)


def _image_url(item: dict) -> str:
    for image in item.get("images") or []:
        if isinstance(image, dict) and image.get("url"):
            return str(image["url"])
    return ""


def _product_choices(items: list) -> dict:
    return {
        "kind": "product_choices",
        "items": [
            {
                "number": number,
                "name": item["name"],
                "price": _price(item["unit_price"]),
                "description": item.get("description") or "",
                "image_url": _image_url(item),
            }
            for number, item in enumerate(items, 1)
        ],
    }


def _order_summary(draft: dict) -> dict:
    return {
        "kind": "order_summary",
        "name": draft.get("product_name") or draft["sku"],
        "sku": draft["sku"],
        "quantity": int(draft["quantity"]),
        "unit_price": _price(draft["price"]),
        "total": _price(draft["total"]),
        "image_url": draft.get("image_url") or "",
    }
