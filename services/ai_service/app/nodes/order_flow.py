from typing import Literal, Optional
from uuid import uuid4
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.runnables import RunnableConfig
from langchain_groq import ChatGroq
from langgraph.graph import END
from langgraph.config import get_stream_writer
from langgraph.types import Command, interrupt
from pydantic import BaseModel, Field
from app.core.config import settings
from app.services.agent_state import AgentState
from app.services.agent_tools import call_service, fetch_item_details
from app.core.schemas import OrderSlots

CANCEL_WORDS = {"cancel", "never mind", "nevermind", "stop", "no thanks", "no"}
CONFIRM_WORDS = {"yes", "y", "confirm", "yeah", "yep", "sure", "go ahead", "do it"}

slot_llm = ChatGroq(model="openai/gpt-oss-safeguard-20b",api_key=settings.LLM_API_KEY,temperature=0,).with_structured_output(OrderSlots)

async def collect_order_details(state: AgentState, config: RunnableConfig) -> Command[Literal["validate_item", "collect_order_details", "__end__"]]:
    writer = get_stream_writer()
    writer({"type": "thought", "node": "collect_order_details", "message": "Checking the product and quantity for your order..."})
    draft = dict(state.get("order_draft") or {})
    missing = []

    if not draft.get("product_query") and not draft.get("sku"):
        missing.append("which product you'd like (name or description)")
    if not draft.get("quantity"):
        missing.append("how many you'd like")

    if not missing:
        return Command(goto="validate_item")

    writer({"type": "thought", "node": "collect_order_details", "message": "I need a few more details to continue."})
    answer = interrupt({"question": f"Sure, could you tell me {' and '.join(missing)}?"})

    if isinstance(answer, str) and answer.strip().lower() in CANCEL_WORDS:
        return Command(goto=END,update={"order_draft": {}, "messages": [AIMessage(content="No problem, I've cancelled that.")]},)

    slots: OrderSlots = await slot_llm.ainvoke([HumanMessage(content=str(answer))], config) # this extracts product_query and quantity from the user's answer

    if slots.product_query:
        draft["product_query"] = slots.product_query

    if slots.quantity:
        draft["quantity"] = slots.quantity

    return Command(goto="collect_order_details", update={"order_draft": draft})

async def validate_item(state: AgentState) -> Command[Literal["validate_item", "check_wallet", "collect_order_details", "__end__"]]:
    writer = get_stream_writer()
    writer({"type": "thought", "node": "validate_item", "message": "Checking your product selection..."})

    draft = dict(state.get("order_draft") or {})
    query = draft.get("product_query")
    
    if "search_matches" in draft:
        result = {"response": draft["search_matches"]}

    else:
        writer({"type": "thought", "node": "validate_item", "message": "Searching the catalog for matching products..."})
        result = await fetch_item_details(query,  state["access_token"])
        
        if not result.get("error") and len(result.get("response") or []) > 1:
            draft["search_matches"] = result["response"]
            return Command(goto="validate_item", update={"order_draft": draft})

    if result.get("error"):
        return Command(goto=END, update={"messages": [AIMessage(content="I couldn't search the catalog right now. Please try again in a moment.")]})

    items = result.get("response") or []
    if not items:
        return Command(goto="collect_order_details",update={"order_draft": {"quantity": draft.get("quantity")},"messages": [AIMessage(content=f'I couldn\'t find a match for "{query}".'"Could you describe the product or try another name?")],},)
    
    if len(items) > 1:
        writer({"type": "thought", "node": "validate_item", "message": "Several products match. Please choose one from the options."})
        answer = interrupt({
            "question": "I found several products. Which one would you like? Reply with its number, or cancel.",
            "options": [
                {"number": i, "name": item["name"], "price": item["unit_price"],
                 "description": item.get("description", "")}
                for i, item in enumerate(items, 1)]})

        if isinstance(answer, str) and answer.strip().lower() in CANCEL_WORDS:
            return Command(goto=END, update={"order_draft": {}, "messages": [AIMessage(content="No problem, I've cancelled that. What would you like to do next?")]})

        choice = str(answer).strip()
        if not choice.isdecimal() or not 1 <= int(choice) <= len(items):
            return Command(goto="collect_order_details", update={"order_draft": {"quantity": draft.get("quantity")},"messages": [AIMessage(content="I couldn't identify that selection. Please describe the product you'd like.")]})

        item = items[int(choice) - 1]
    else:
        item = items[0]

    draft.pop("search_matches", None)
    draft["sku"] = item["sku"]
    draft["product_name"] = item["name"]
    draft["price"] = item["unit_price"]
    return Command(goto="check_wallet", update={"order_draft": draft})

async def check_wallet(state: AgentState) -> Command[Literal["confirm_order", "__end__"]]:
    writer = get_stream_writer()
    writer({"type": "thought", "node": "check_wallet", "message": "Checking whether your wallet can cover this order..."})
    draft = dict(state.get("order_draft") or {})
    total = draft["price"] * draft["quantity"]
    url = f"{settings.PAYMENT_BASE_URL}/wallets/buyer"
    wallet = await call_service("GET", url, state["access_token"])

    if wallet.get("error"):
        return Command(goto=END,update={"messages": [AIMessage(content="I couldn't check your wallet balance right now, so I've paused the order.")]},)

    balance = wallet["current_balance"]
    if balance < total:
        return Command(goto=END,
            update={
                "order_draft": {},
                "messages": [AIMessage(
                    content=f"This order comes to {total:.2f}, but your wallet balance is only "
                            f"{balance:.2f}. That's not enough to cover it."
                )],
            },
        )

    return Command(goto="confirm_order", update={"order_draft": {**draft, "total": total}})


async def confirm_order(state: AgentState) -> Command[Literal["place_order", "__end__"]]:
    writer = get_stream_writer()
    writer({"type": "thought", "node": "confirm_order", "message": "Your order summary is ready for confirmation."})
    draft = dict(state.get("order_draft") or {})
    answer = interrupt({
        "question": f"That's {draft['quantity']} x {draft.get('product_name', draft['sku'])} for a total of "
                    f"{draft['total']:.2f}. Should I place the order?"
    })

    if isinstance(answer, str) and answer.strip().lower() in CONFIRM_WORDS:
        return Command(goto="place_order")

    return Command(
        goto=END,
        update={"order_draft": {}, "messages": [AIMessage(content="Okay, I won't place that order.")]},
    )


async def place_order_node(state: AgentState) -> Command[Literal["__end__"]]:
    writer = get_stream_writer()
    writer({"type": "thought", "node": "place_order_node", "message": "Submitting your order..."})
    draft = dict(state.get("order_draft") or {})
    idempotency_key = str(uuid4())
    url = f"{settings.ORDER_BASE_URL}/api/v1/order/place/{idempotency_key}"
    payload = {"sku": draft["sku"], "quantity": draft["quantity"]}
    if draft.get("delivery_address_id"):
        payload["delivery_address_id"] = draft["delivery_address_id"]

    result = await call_service("POST", url, state["access_token"], json=payload)

    if result.get("error"):
        message = "I couldn't place the order — please try again in a moment."
    else:
        message = f"Done! I've placed your order for {draft['quantity']} x {draft.get('product_name', draft['sku'])}."

    return Command(goto=END, update={"order_draft": {}, "messages": [AIMessage(content=message)]})

async def wallet_balance_node(state: AgentState) -> Command[Literal["__end__"]]:
    writer = get_stream_writer()
    writer({"type": "thought", "node": "wallet_balance_node", "message": "Retrieving your wallet balance..."})
    writer({"type": "thought", "node": "wallet_balance_node", "message": "Hold on a sec..."})
    url = f"{settings.PAYMENT_BASE_URL}/wallets/buyer"
    wallet = await call_service("GET", url, state["access_token"])
    if wallet.get("error"):
        writer({"type": "thought", "node": "wallet_balance_node", "message": "Oops! Something is going on..."})
        message = "I couldn't check your wallet balance right now."
    else:
        message = f"Your wallet balance is {wallet['current_balance']:.2f}."
    return Command(goto=END, update={"messages": [AIMessage(content=message)]})