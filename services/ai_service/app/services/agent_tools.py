from typing import Annotated, Optional
from uuid import uuid4
import aiohttp
from langchain_core.tools import tool
from langgraph.prebuilt import InjectedState
from app.core.config import settings
from app.core.logging import logger
from app.services.agent_state import AgentState


async def _call_service(method: str,url: str,access_token: str,json: Optional[dict] = None,params: Optional[dict] = None) -> dict:
    headers = {"Authorization": f"Bearer {access_token}"} if access_token else {}
    try:
        async with aiohttp.ClientSession() as session:
            async with session.request(method, url, json=json, params=params, headers=headers) as response:
                response.raise_for_status()
                return await response.json()
    except aiohttp.ClientResponseError as e:
        logger.error(f"{method} {url} failed: {e.status} - {e.message}")
        return {"error": True, "status": e.status, "message": e.message}
    except aiohttp.ClientError as e:
        logger.error(f"{method} {url} connection error: {e}")
        return {"error": True, "status": 503, "message": "Service unavailable"}


def _require_admin(state: AgentState) -> Optional[dict]:
    if not state.get("is_admin"):
        return {"error": True, "status": 403, "message": "This action requires admin access."}
    return None

# NOTE: Customer Tools

@tool
async def make_order(product_id: str,quantity: int,state: Annotated[AgentState, InjectedState],delivery_address_id: Optional[str] = None,) -> dict:
    idempotency_key = str(uuid4())
    url = f"{settings.ORDER_BASE_URL}/api/v1/order/place/{idempotency_key}"
    payload = {"sku": product_id, "quantity": quantity}
    if delivery_address_id:
        payload["delivery_address_id"] = delivery_address_id ## update this
    return await _call_service("POST", url, state["access_token"], json=payload)


@tool
async def reorder(order_id: str, state: Annotated[AgentState, InjectedState]) -> dict:
    idempotency_key = str(uuid4())
    url = f"{settings.ORDER_BASE_URL}/api/v1/order/{order_id}/reorder/{idempotency_key}"
    return await _call_service("POST", url, state["access_token"])


@tool
async def change_delivery_address(order_id: str, address_id: str, state: Annotated[AgentState, InjectedState]) -> dict:
    url = f"{settings.ORDER_BASE_URL}/api/v1/order/{order_id}/address"
    return await _call_service("PATCH", url, state["access_token"], json={"address_id": address_id})

@tool
async def change_order_quantity(order_id: str, item_id: str, quantity: int, state: Annotated[AgentState, InjectedState]) -> dict:
    url = f"{settings.ORDER_BASE_URL}/api/v1/order/{order_id}/items/{item_id}"
    return await _call_service("PATCH", url, state["access_token"], json={"quantity": quantity})

@tool
async def get_order_analytics(state: Annotated[AgentState, InjectedState]) -> dict:
    """Get the signed-in customer's own order analytics: order count, total spend, most-ordered products."""
    url = f"{settings.ORDER_BASE_URL}/api/v1/order/analytics"
    return await _call_service("GET", url, state["access_token"])

# NOTE: Admin Tools

@tool
async def get_user_count(state: Annotated[AgentState, InjectedState]) -> dict:
    """Get the total number of registered users (admin only)."""
    if denial := _require_admin(state):
        return denial
    url = f"{settings.AUTH_BASE_URL}/api/v1/auth/admin/users/count" ## change this url
    return await _call_service("GET", url, state["access_token"])


@tool
async def get_order_statistics(period: str, state: Annotated[AgentState, InjectedState]) -> dict:
    if denial := _require_admin(state):
        return denial
    url = f"{settings.ORDER_BASE_URL}/api/v1/order/admin/statistics"
    return await _call_service("GET", url, state["access_token"], params={"period": period})


@tool
async def get_customer_statistics(period: str, state: Annotated[AgentState, InjectedState]) -> dict:
    if denial := _require_admin(state):
        return denial
    url = f"{settings.AUTH_BASE_URL}/api/v1/auth/admin/customers/statistics" ## create this endpoint
    return await _call_service("GET", url, state["access_token"], params={"period": period})

@tool
async def get_low_stock_products(state: Annotated[AgentState, InjectedState]) -> dict:
    """List products whose stock has fallen below the low-stock threshold (admin only)."""
    if denial := _require_admin(state):
        return denial
    url = f"{settings.INVENTORY_BASE_URL}/api/v1/inventory/admin/low-stock"
    return await _call_service("GET", url, state["access_token"])


@tool
async def get_out_of_stock_products(state: Annotated[AgentState, InjectedState]) -> dict:
    """List products that are completely out of stock (admin only)."""
    if denial := _require_admin(state):
        return denial
    url = f"{settings.INVENTORY_BASE_URL}/api/v1/inventory/admin/out-of-stock"
    return await _call_service("GET", url, state["access_token"])


@tool
async def get_inventory_summary(state: Annotated[AgentState, InjectedState]) -> dict:
    """Get a store-wide inventory summary: total SKUs, total units, total inventory value (admin only)."""
    if denial := _require_admin(state):
        return denial
    url = f"{settings.INVENTORY_BASE_URL}/api/v1/inventory/admin/summary"
    return await _call_service("GET", url, state["access_token"])


@tool
async def get_failed_order_statistics(period: str, state: Annotated[AgentState, InjectedState]) -> dict:
    if denial := _require_admin(state):
        return denial
    url = f"{settings.ORDER_BASE_URL}/api/v1/order/admin/failed-statistics"
    return await _call_service("GET", url, state["access_token"], params={"period": period})


CUSTOMER_TOOLS = [
    make_order,
    reorder,
    change_delivery_address,
    change_order_quantity,
    get_order_analytics,
]

ADMIN_TOOLS = [
    get_user_count,
    get_order_statistics,
    get_customer_statistics,
    get_low_stock_products,
    get_out_of_stock_products,
    get_inventory_summary,
    get_failed_order_statistics,
]

tools = CUSTOMER_TOOLS + ADMIN_TOOLS