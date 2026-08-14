from pydantic import BaseModel, RootModel
from enum import Enum
from typing import Union

class InventorySchema(BaseModel):
    name: Union[str,None]
    description: Union[str,None]
    unit_price: Union[float,None]
    sku: Union[str,None]
    available_quantity: Union[int, None]
    reserved_quantity: Union[int, None]

class InventorySchemaList(RootModel[list[InventorySchema]]):
    pass

class InventoryDeleteSchema(BaseModel):
    sku: str

class Roles(Enum):
    ADMIN = "admin"
    CUSTOMER = "customer"
    EMPLOYEE = "employee"
    INVENTORY_MANAGER = "inventory_manager"


class InventoryReserve(BaseModel):
    sku: Union[str,None]
    reserved_quantity: Union[int, None]


