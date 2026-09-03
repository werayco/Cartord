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
    BUYER = "buyer"
    SELLER = "seller"

class WalletResponse(BaseModel):
    initial_amount: int
    current_balance: int