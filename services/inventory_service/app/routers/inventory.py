
from uuid import UUID

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.controllers.inventory_controller import InventoryCRUD
from app.core.schemas import (
    InventoryCreateResponse,
    InventoryCreateSchema,
    InventoryReserve,
    InventoryResponse,
    InventorySchema,
    ProductImageCompleteRequest,
    ProductImageResponse,
    ProductImageUploadRequest,
    ProductImageUploadResponse,
)
from app.core.utils import get_current_user
from app.db.session import get_db
from app.services.product_image_service import (
    complete_upload,
    create_upload,
    delete_image,
)

inventory_router = APIRouter(prefix="/api/v1/inventory", tags=["inventory"])


@inventory_router.post("/", response_model=InventoryCreateResponse)
async def add_inventory_item(
    inventory: InventoryCreateSchema,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return await InventoryCRUD.add_inventory_item(db, inventory, current_user)


@inventory_router.put("/")
async def update_inventory_item(
    inventory: InventorySchema,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return await InventoryCRUD.update_inventory_item(db, inventory, current_user)


@inventory_router.delete("/")
async def delete_inventory_item(
    inventory: InventorySchema,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return await InventoryCRUD.delete_inventory_item(db, inventory, current_user)


@inventory_router.get("/", response_model=list[InventoryResponse])
async def get_inventory_item(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return await InventoryCRUD.get_inventory_item(db, current_user)


@inventory_router.patch("/reserve")
async def reserve_item(
    inventory: InventoryReserve, req: Request, db: AsyncSession = Depends(get_db)
):
    return await InventoryCRUD.reserve_inventory(inventory, req, db)


@inventory_router.post(
    "/{sku}/images/upload-url", response_model=ProductImageUploadResponse
)
async def create_product_image_upload(
    sku: str,
    image: ProductImageUploadRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return await create_upload(db, sku, image, current_user)


@inventory_router.post(
    "/{sku}/images/complete", response_model=ProductImageResponse
)
async def complete_product_image_upload(
    sku: str,
    image: ProductImageCompleteRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return await complete_upload(db, sku, image.image_id, current_user)


@inventory_router.delete("/{sku}/images/{image_id}")
async def delete_product_image(
    sku: str,
    image_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return await delete_image(db, sku, image_id, current_user)
