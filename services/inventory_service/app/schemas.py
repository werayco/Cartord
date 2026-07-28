from pydantic import BaseModel, RootModel
from enum import Enum
from typing import Union

class InventorySchema(BaseModel):
    name: Union[str,None]
    description: Union[str,None]
    price: Union[float,None]
    sku: Union[str,None]
    quantity: Union[int, None]
    reserved_quantity: Union[int, None]

class InventorySchemaList(RootModel[list[InventorySchema]]):
    pass

class InventoryDeleteSchema(BaseModel):
    sku: str

class Roles(Enum):
    ADMIN = "admin"
    CUSTOMER = "customer"
    EMPLOYEE = "employee"

