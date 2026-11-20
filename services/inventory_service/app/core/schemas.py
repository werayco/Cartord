from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, RootModel


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


class InventoryCommit(BaseModel):
    sku: str
    quantity: int


class InventoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str
    description: str | None = None
    sku: str
    unit_price: float
    available_quantity: int
    reserved_quantity: int = 0
    created_at: datetime
    images: list["ProductImageResponse"] = Field(default_factory=list)


class ProductImageResponse(BaseModel):
    id: UUID
    url: str
    alt_text: str | None = None
    sort_order: int


class ProductImageUploadRequest(BaseModel):
    content_type: str
    file_size: int = Field(gt=0)
    alt_text: str | None = Field(default=None, max_length=255)


class ProductImageUploadResponse(BaseModel):
    image_id: UUID
    object_key: str
    upload_url: str
    content_type: str


class ProductImageCompleteRequest(BaseModel):
    image_id: UUID


class InventoryAdminItem(InventoryResponse):
    description: str | None = None
    reserved_quantity: int
    sellable_quantity: int


class InventorySummaryResponse(BaseModel):
    total_skus: int
    total_units: int
    total_inventory_value: float
