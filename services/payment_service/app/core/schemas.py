import uuid
from enum import Enum

from pydantic import BaseModel


class WalletCreate(BaseModel):
    customer_id: uuid.UUID


class PaymentStatus(Enum):
    FAILED = "FAILED"
    SUCCEEDED = "SUCCESS"
    PENDING = "PENDING"


class Roles(Enum):
    BUYER = "buyer"
    SELLER = "seller"


class WalletResponse(BaseModel):
    initial_amount: float
    current_balance: float
