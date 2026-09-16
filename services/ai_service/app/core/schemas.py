from enum import Enum
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field
from typing import Literal, Optional

class AIRequest(BaseModel):
    query: str

class Conversation(BaseModel):
    user_id: UUID

class Roles(Enum):
    ADMIN = "admin"
    SELLER = "seller"

class IntentClassification(BaseModel):
    intent: Literal[
        "place_order",
        "check_balance",
        "reorder",
        "change_address",
        "change_quantity",
        "order_analytics",
        "faq",
        "chitchat",
    ] = Field(description="The single best-matching intent for the customer's latest message.")
    product_query: Optional[str] = Field(
        default=None, description="Product name or SKU the customer explicitly mentioned, if any."
    )
    quantity: Optional[int] = Field(
        default=None, description="Quantity the customer explicitly mentioned, if any."
    )

class OrderSlots(BaseModel):
    product_query: Optional[str] = Field(default=None, description="Product name or SKU, if mentioned.")
    quantity: Optional[int] = Field(default=None, description="Quantity, if mentioned.")
