from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, RootModel


class InventorySchema(BaseModel):
    name: str | None = None
    description: str | None = None
    unit_price: float | None = None
    sku: str | None = None
    available_quantity: int | None = None
    reserved_quantity: int | None = None


class InventoryCreateSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    description: str | None = None
    unit_price: float
    available_quantity: int = 0
    reserved_quantity: int = 0


class InventoryCreateResponse(BaseModel):
    message: str
    sku: str


class InventorySchemaList(RootModel[list[InventoryCreateSchema]]):
    pass


class InventoryDeleteSchema(BaseModel):
    sku: str


class Roles(Enum):
    ADMIN = "admin"
    SELLER = "seller"


class InventoryReserve(BaseModel):
    sku: str | None
    reserved_quantity: int | None


class InventoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str
    sku: str
    unit_price: float
    available_quantity: int
    created_at: datetime


class InventoryAdminItem(InventoryResponse):
    description: str | None = None
    reserved_quantity: int
    sellable_quantity: int


class InventorySummaryResponse(BaseModel):
    total_skus: int
    total_units: int
    total_inventory_value: float
