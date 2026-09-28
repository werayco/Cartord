from typing import Annotated, Optional
from uuid import uuid4
import aiohttp
from langchain_core.tools import tool
from langgraph.types import interrupt
from langgraph.config import get_stream_writer
from langgraph.prebuilt import InjectedState
from app.core.config import settings
from app.core.logging import logger
from app.db.session import AsyncSessionLocal
from app.services.agent_state import AgentState
from app.services.rag_pipeline import RAGPipeline
from datetime import timedelta
from aiobreaker import CircuitBreaker, CircuitBreakerError

breaker = CircuitBreaker(fail_max=5, timeout_duration=timedelta(seconds=30))

async def call_service(method: str, url: str, access_token: str, json: Optional[dict] = None, params: Optional[dict] = None) -> dict:
    headers = {"Authorization": f"Bearer {access_token}"} if access_token else {}
    async def _do_request():
        async with aiohttp.ClientSession() as session:
            async with session.request(method, url, json=json, params=params, headers=headers) as response:
                response.raise_for_status()
                return await response.json()
    try:
        return await breaker.call_async(_do_request)
    except CircuitBreakerError:
        logger.error(f"{method} {url} short-circuited - breaker open")
        return {"error": True, "status": 503, "message": "Service temporarily unavailable, please try again shortly."}
    except aiohttp.ClientResponseError as e:
        logger.error(f"{method} {url} failed: {e.status} - {e.message}")
        return {"error": True, "status": e.status, "message": e.message}
    except aiohttp.ClientError as e:
        logger.error(f"{method} {url} connection error: {e}")
        return {"error": True, "status": 503, "message": "Service unavailable"}

async def fetch_item_details(query: str, access_token: str) -> dict:
    """Search the catalog by product name; return ranked matches with their SKUs."""
    url = f"{settings.SEARCH_BASE_URL}/api/v1/search/items"
    return await call_service("GET", url, access_token, params={"query": query})

@tool
async def change_delivery_address(access_token: Annotated[str, InjectedState("access_token")],shipping_address: Optional[str] = None) -> dict:
    """Update the signed-in customer's default shipping address on their account.
    Pass shipping_address only if the customer already stated the new address in
    their message. Leave it unset if they only said they want to change it without
    giving the new address, you'll be prompted and can retry with the value."""

    if not shipping_address:
        answer = interrupt({"question": "Sure, what would you like your new shipping address to be?"})
        shipping_address = str(answer)

    writer = get_stream_writer()
    writer({"type": "thought", "message": "Updating your shipping address..."})
    url = f"{settings.AUTH_BASE_URL}/api/v1/auth/buyer/update"
    result = await call_service("PATCH", url, access_token, json={"shipping_address": shipping_address})
    writer({"type": "thought", "message": "Your shipping address has been updated." if not result.get("error") else "I couldn't update your shipping address."})
    return result

@tool
async def get_order_summary(access_token: Annotated[str, InjectedState("access_token")]) -> dict:
    """Get the signed-in customer's own order summary and analytics, including total orders, delivered orders, total spend, active orders, failed or cancelled orders, and most-ordered products."""
    writer = get_stream_writer()
    writer({"type": "thought", "message": "Analyzing your order history..."})

    url = f"{settings.ORDER_BASE_URL}/api/v1/order/summary"
    result = await call_service("GET", url, access_token)
    writer({"type": "thought", "message": "Almost Done..."})
    writer({"type": "thought", "message": "Your order analytics are ready." if not result.get("error") else "I couldn't retrieve your order analytics."})
    return result

@tool
async def get_wallet_balance(access_token: Annotated[str, InjectedState("access_token")]) -> dict:
    """Get the signed-in customer's current wallet balance."""
    writer = get_stream_writer()
    writer({"type": "thought", "message": "Checking your wallet balance..."})
    url = f"{settings.PAYMENT_BASE_URL}/wallets/buyer"
    writer({"type": "thought", "message": "Hold on a sec..."})
    writer({"type": "thought", "message": "Working on it..."})
    result = await call_service("GET", url, access_token)
    if result.get("error"):
        return {"error": result.get("message", "Wallet balance unavailable.")}
    return f"Current_balance of the user is {result['current_balance']}"

@tool
async def get_faq_response(question: str) -> dict:
    """Answer a general store/product FAQ question about Cartord using the store's knowledge base."""
    writer = get_stream_writer()
    writer({"type": "thought", "message": "Looking that up in the store knowledge base..."})
    async with AsyncSessionLocal() as db:
        documents = await RAGPipeline.retrieve_documents(question, db)
        result = {"document_text": [doc.content for doc in documents]}
    writer({"type": "thought", "message": "I found the relevant information."})
    return result

CUSTOMER_TOOLS = [
    change_delivery_address,
    get_order_summary,
    get_wallet_balance,
    get_faq_response,
]

tools = CUSTOMER_TOOLS