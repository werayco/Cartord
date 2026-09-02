from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.controllers.admin_controller import AdminController
from app.core.schemas import CustomerStatisticsResponse, UserCountResponse
from app.core.utils import get_admin_user
from app.db.session import get_db
from app.models.seller import Seller

admin_router = APIRouter(prefix="/api/v1/auth/admin", tags=["admin"])

@admin_router.get("/users/count", response_model=UserCountResponse)
async def get_user_count(db: AsyncSession = Depends(get_db),_: Seller = Depends(get_admin_user),):
    return await AdminController.get_user_count(db)


@admin_router.get("/customers/statistics", response_model=CustomerStatisticsResponse)
async def get_customer_statistics(period: str = "all",db: AsyncSession = Depends(get_db),_: Seller = Depends(get_admin_user),):
    return await AdminController.get_customer_statistics(period, db)
