from pydantic import BaseModel, ConfigDict, Field, field_validator
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



class ConversationRename(BaseModel):
    title: str = Field(min_length=1, max_length=100)

    @field_validator("title")
    @classmethod
    def clean_title(cls, v: str) -> str:
        v = " ".join(v.split())
        if not v:
            raise ValueError("title cannot be blank")
        return v