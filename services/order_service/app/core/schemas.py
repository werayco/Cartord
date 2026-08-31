from pydantic import BaseModel
from pydantic import BaseModel
from enum import Enum

class OrderPayload(BaseModel):
    sku: str
    quantity: int

class Roles(Enum):
    ADMIN = "admin"
    SELLER = "seller"

class OrderStatus(Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"