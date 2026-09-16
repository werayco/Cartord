from typing import Annotated
from typing_extensions import TypedDict, NotRequired
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
from uuid import UUID

class OrderDraft(TypedDict, total=False):
    product_query: str
    product_name: str
    search_matches: list[dict]
    sku: str
    quantity: int
    price: float
    total: float
    delivery_address_id: str


class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    user_id: UUID
    access_token: str
    users_name: str
    intent: NotRequired[str]
    order_draft: NotRequired[OrderDraft]