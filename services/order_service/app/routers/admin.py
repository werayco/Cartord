from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.controllers.admin_controller import AdminController
from app.core.schemas import FailedOrderStatisticsResponse, OrderStatisticsResponse
from app.core.utils import get_admin_user
from app.db.session import get_db

admin_router = APIRouter(prefix="/api/v1/order/admin", tags=["admin"])

@admin_router.get("/statistics", response_model=OrderStatisticsResponse)
async def get_order_statistics(period: str = "all",db: AsyncSession = Depends(get_db),_: dict = Depends(get_admin_user)):
    return await AdminController.get_order_statistics(period, db)

@admin_router.get("/failed-statistics", response_model=FailedOrderStatisticsResponse)
async def get_failed_order_statistics(period: str = "all",db: AsyncSession = Depends(get_db),_: dict = Depends(get_admin_user),):
    return await AdminController.get_failed_order_statistics(period, db)
