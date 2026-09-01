from typing import Annotated, Optional
from uuid import uuid4
import aiohttp
from langchain_core.tools import tool
from langgraph.prebuilt import InjectedState
from app.core.config import settings
from app.core.logging import logger
from app.db.session import AsyncSessionLocal
from app.services.agent_state import AgentState
from app.services.rag_pipeline import RAGPipeline

async def call_service(method: str, url: str, access_token: str, json: Optional[dict] = None, params: Optional[dict] = None) -> dict:
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
async def make_order(product_id: str, quantity: int, state: Annotated[AgentState, InjectedState], delivery_address_id: Optional[str] = None) -> dict:
    """Place an order for a product on behalf of the signed-in customer."""
    idempotency_key = str(uuid4())
    url = f"{settings.ORDER_BASE_URL}/api/v1/order/place/{idempotency_key}"
    payload = {"sku": product_id, "quantity": quantity}
    if delivery_address_id:
        payload["delivery_address_id"] = delivery_address_id  ## still needs order_service to accept this field
    return await call_service("POST", url, state["access_token"], json=payload)

@tool
async def reorder(order_id: str, state: Annotated[AgentState, InjectedState]) -> dict:
    """Reorder a previous order, identified by its order ID, for the signed-in customer."""
    idempotency_key = str(uuid4())
    url = f"{settings.ORDER_BASE_URL}/api/v1/order/{order_id}/reorder/{idempotency_key}" ## endpoint doesn't exist yet
    return await call_service("POST", url, state["access_token"])

@tool
async def change_delivery_address(order_id: str, address_id: str, state: Annotated[AgentState, InjectedState]) -> dict:
    """Change the delivery address for an existing order belonging to the signed-in customer."""
    url = f"{settings.ORDER_BASE_URL}/api/v1/order/{order_id}/address" ## endpoint doesn't exist yet
    return await call_service("PATCH", url, state["access_token"], json={"address_id": address_id})

@tool
async def change_order_quantity(order_id: str, item_id: str, quantity: int, state: Annotated[AgentState, InjectedState]) -> dict:
    """Change the quantity of a specific item within an existing order."""
    url = f"{settings.ORDER_BASE_URL}/api/v1/order/{order_id}/items/{item_id}"
    return await call_service("PATCH", url, state["access_token"], json={"quantity": quantity})

@tool
async def get_order_analytics(state: Annotated[AgentState, InjectedState]) -> dict:
    """Get the signed-in customer's own order analytics: order count, total spend, most-ordered products."""
    url = f"{settings.ORDER_BASE_URL}/api/v1/order/analytics" ## endpoint doesn't exist yet
    return await call_service("GET", url, state["access_token"])

@tool
async def get_faq_response(question: str) -> dict:
    """Answer a general store/product FAQ question using the store's knowledge base."""
    async with AsyncSessionLocal() as db:
        documents = await RAGPipeline.retrieve_documents(question, db)
        return {"document_text": [doc.content for doc in documents]}

# NOTE: Admin Tools

@tool
async def get_user_count(state: Annotated[AgentState, InjectedState]) -> dict:
    """Get the total number of registered users on the platform (admin only)."""
    if denial := _require_admin(state):
        return denial
    url = f"{settings.AUTH_BASE_URL}/api/v1/auth/admin/users/count"  ## endpoint doesn't exist yet
    return await call_service("GET", url, state["access_token"])

@tool
async def get_order_statistics(period: str, state: Annotated[AgentState, InjectedState]) -> dict:
    """Get store-wide order statistics for a given period (admin only)."""
    if denial := _require_admin(state):
        return denial
    url = f"{settings.ORDER_BASE_URL}/api/v1/order/admin/statistics"  ## endpoint doesn't exist yet
    return await call_service("GET", url, state["access_token"], params={"period": period})

@tool
async def get_customer_statistics(period: str, state: Annotated[AgentState, InjectedState]) -> dict:
    """Get store-wide customer statistics for a given period (admin only)."""
    if denial := _require_admin(state):
        return denial
    url = f"{settings.AUTH_BASE_URL}/api/v1/auth/admin/customers/statistics"  ## endpoint doesn't exist yet
    return await call_service("GET", url, state["access_token"], params={"period": period})

@tool
async def get_low_stock_products(state: Annotated[AgentState, InjectedState]) -> dict:
    """List products whose stock has fallen below the low-stock threshold (admin only)."""
    if denial := _require_admin(state):
        return denial
    url = f"{settings.INVENTORY_BASE_URL}/api/v1/inventory/admin/low-stock"  ## endpoint doesn't exist yet
    return await call_service("GET", url, state["access_token"])

@tool
async def get_out_of_stock_products(state: Annotated[AgentState, InjectedState]) -> dict:
    """List products that are completely out of stock (admin only)."""
    if denial := _require_admin(state):
        return denial
    url = f"{settings.INVENTORY_BASE_URL}/api/v1/inventory/admin/out-of-stock"  ## endpoint doesn't exist yet
    return await call_service("GET", url, state["access_token"])

@tool
async def get_inventory_summary(state: Annotated[AgentState, InjectedState]) -> dict:
    """Get a store-wide inventory summary: total SKUs, total units, total inventory value (admin only)."""
    if denial := _require_admin(state):
        return denial
    url = f"{settings.INVENTORY_BASE_URL}/api/v1/inventory/admin/summary"  ## endpoint doesn't exist yet
    return await call_service("GET", url, state["access_token"])

@tool
async def get_failed_order_statistics(period: str, state: Annotated[AgentState, InjectedState]) -> dict:
    """Get statistics on failed orders for a given period (admin only)."""
    if denial := _require_admin(state):
        return denial
    url = f"{settings.ORDER_BASE_URL}/api/v1/order/admin/failed-statistics"  ## endpoint doesn't exist yet
    return await call_service("GET", url, state["access_token"], params={"period": period})

CUSTOMER_TOOLS = [
    make_order,
    reorder,
    change_delivery_address,
    change_order_quantity,
    get_order_analytics,
    get_faq_response,
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