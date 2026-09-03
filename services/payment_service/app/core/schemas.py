from pydantic import BaseModel
from enum import Enum
import uuid

class WalletCreate(BaseModel):
    customer_id: uuid.UUID

class PaymentStatus(Enum):
    FAILED = "FAILED"
    SUCCEEDED = "SUCCESS"
    PENDING = "PENDING"

class Roles(Enum):
    buyer = "buyer"
    SELLER = "seller"

class WalletResponse(BaseModel):
    id: uuid.UUID
    customer_id: uuid.UUID
    initial_amount: int
    current_balance: int