from enum import Enum
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


class AIRequest(BaseModel):
    query: str


class Conversation(BaseModel):
    user_id: UUID


class Roles(Enum):
    ADMIN = "admin"
    SELLER = "seller"


class IntentClassification(BaseModel):
    intent: Literal["place_order", "check_balance", "general"] = Field(
        description="The single best-matching intent for the customer's latest message."
    )
    product_query: str | None = Field(
        default=None,
        description="Product name or SKU the customer explicitly mentioned, if any.",
    )
    quantity: int | None = Field(
        default=None, description="Quantity the customer explicitly mentioned, if any."
    )


class OrderSlots(BaseModel):
    product_query: str | None = Field(
        default=None, description="Product name or SKU, if mentioned."
    )
    quantity: int | None = Field(
        default=None, description="Quantity (it is an integer), if mentioned."
    )
