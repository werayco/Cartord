from pydantic import BaseModel, RootModel, ConfigDict
from enum import Enum
from typing import Union
from datetime import datetime

class InventorySchema(BaseModel):
    name: Union[str, None] = None
    description: Union[str, None] = None
    unit_price: Union[float, None] = None
    sku: Union[str, None] = None
    available_quantity: Union[int, None] = None
    reserved_quantity: Union[int, None] = None

class InventorySchemaList(RootModel[list[InventorySchema]]):
    pass

class InventoryDeleteSchema(BaseModel):
    sku: str

class Roles(Enum):
    ADMIN = "admin"
    SELLER = "seller"

class InventoryReserve(BaseModel):
    sku: Union[str,None]
    reserved_quantity: Union[int, None]

class InventoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str
    sku: str
    unit_price: float
    available_quantity: int
    created_at: datetime

