from pydantic import BaseModel
from enum import Enum
import uuid

class WalletCreate(BaseModel):
    customer_id: uuid.UUID

class PaymentStatus(Enum):
    FAILED = "failed"
    SUCCEEDED = "success"
    PENDING = "pending"