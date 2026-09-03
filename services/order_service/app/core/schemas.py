from pydantic import BaseModel
from pydantic import BaseModel
from enum import Enum

class OrderPayload(BaseModel):
    sku: str
    quantity: int

class OrderResponse(BaseModel):
    order_id: str
    quantity: int
    unit_price: float
    status: str

class Roles(Enum):
    ADMIN = "admin"
    SELLER = "seller"

class OrderStatus(Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
    FAILED = "failed"

class OrderStatisticsResponse(BaseModel):
    period: str
    total_orders: int
    total_items: int
    total_revenue: float
    average_order_value: float
    orders_by_status: dict[str, int]

class FailedOrderStatisticsResponse(BaseModel):
    period: str
    failed_orders: int
    failed_items: int
    failed_revenue: float