from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.controllers.admin_controller import AdminController
from app.core.schemas import InventoryAdminItem, InventorySummaryResponse
from app.core.utils import get_admin_user
from app.db.session import get_db

admin_router = APIRouter(prefix="/api/v1/inventory/admin", tags=["admin"])


@admin_router.get("/low-stock", response_model=list[InventoryAdminItem])
async def get_low_stock(
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_admin_user),
):
    return await AdminController.get_low_stock(db)


@admin_router.get("/out-of-stock", response_model=list[InventoryAdminItem])
async def get_out_of_stock(
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_admin_user),
):
    return await AdminController.get_out_of_stock(db)


@admin_router.get("/summary", response_model=InventorySummaryResponse)
async def get_summary(
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_admin_user),
):
    return await AdminController.get_summary(db)
