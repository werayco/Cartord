from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.schemas import InventorySchema, InventoryReserve
from app.controllers.inventory_controller import InventoryCRUD
from app.utils import get_current_user

inventory_router = APIRouter(prefix="/api/v1/inventory", tags=["inventory"])

@inventory_router.post("/")
async def add_inventory_item(
    inventory: InventorySchema,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    return await InventoryCRUD.add_inventory_item(db, inventory, current_user)

@inventory_router.get("/")
async def get_inventory_item(
    inventory: InventorySchema,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    return await InventoryCRUD.get_inventory_item(db, inventory, current_user)

@inventory_router.put("/")
async def update_inventory_item(
    inventory: InventorySchema,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    return await InventoryCRUD.update_inventory_item(db, inventory, current_user)

@inventory_router.delete("/")
async def delete_inventory_item(
    inventory: InventorySchema,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    return await InventoryCRUD.delete_inventory_item(db, inventory, current_user)

@inventory_router.patch("/reserve")
async def reserve_item(inventory: InventoryReserve, req: Request, db: AsyncSession = Depends(get_db)):
    return await InventoryCRUD.reserve_inventory(inventory, req, db)