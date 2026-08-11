from pydantic import BaseModel
from pydantic import BaseModel, RootModel
from enum import Enum
from typing import Union

class OrderPayload(BaseModel):
    sku: str
    quantity: int

class Roles(Enum):
    ADMIN = "admin"
    CUSTOMER = "customer"
    EMPLOYEE = "employee"

class OrderStatus(Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"