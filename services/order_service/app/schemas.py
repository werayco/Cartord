from pydantic import BaseModel
from pydantic import BaseModel, RootModel
from enum import Enum
from typing import Union

class OrderPayload(BaseModel):
    "Frontend/client sends this payload to the backend, then the backend queries using the sku and retrieve the PR"
    sku: str
    quantity: int

class Roles(Enum):
    ADMIN = "admin"
    CUSTOMER = "customer"
    EMPLOYEE = "employee"

class OrderStatus(str):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"