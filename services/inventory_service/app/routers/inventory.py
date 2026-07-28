from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.schemas import InventorySchema
from app.controllers.inventory_controller import InventoryCRUD
from app.utils import get_current_user_dep
from app.models.employee import Employee

inventory_router = APIRouter(prefix="/api/v1/inventory",tags=["inventory"])

@inventory_router.post("/add")
async def add_inventory_item(db: AsyncSession = Depends(get_db), inventory: InventorySchema = None, current_user: Employee = Depends(get_current_user_dep(Employee))):
    return InventoryCRUD.add_inventory_item(db, inventory, current_user)

@inventory_router.get("/get")
async def get_inventory_item(inventory: InventorySchema, db: AsyncSession = Depends(get_db), current_user: Employee = Depends(get_current_user_dep(Employee))):
    return InventoryCRUD.get_inventory_item(db, inventory, current_user)

@inventory_router.put("/update")
async def update_inventory_item(db: AsyncSession = Depends(get_db), inventory: InventorySchema = None, current_user: Employee = Depends(get_current_user_dep(Employee))):
    return InventoryCRUD.update_inventory_item(db, inventory, current_user)

@inventory_router.delete("/delete")
async def delete_inventory_item(inventory: InventorySchema, db: AsyncSession = Depends(get_db), current_user: Employee = Depends(get_current_user_dep(Employee))):
    return InventoryCRUD.delete_inventory_item(db, inventory, current_user)