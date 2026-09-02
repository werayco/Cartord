from datetime import datetime, timedelta, timezone
from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.schemas import CustomerStatisticsResponse, UserCountResponse
from app.models.buyer import Buyer
from app.models.seller import Seller

_PERIODS = {"day": timedelta(days=1), "week": timedelta(weeks=1), "month": timedelta(days=30), "year": timedelta(days=365)}


def _period_start(period: str) -> datetime | None:
    if period == "all":
        return None
    duration = _PERIODS.get(period)
    if duration is None:
        raise HTTPException(status_code=422, detail="period must be one of: day, week, month, year, all")
    return datetime.now(timezone.utc) - duration


class AdminController:
    @staticmethod
    async def get_user_count(db: AsyncSession) -> UserCountResponse:
        try:
            buyer_count = await db.scalar(select(func.count()).select_from(Buyer))
            seller_count = await db.scalar(select(func.count()).select_from(Seller))
            return UserCountResponse(total_users=(buyer_count or 0) + (seller_count or 0))
        except SQLAlchemyError:
            raise HTTPException(status_code=500, detail="Unable to retrieve user count")

    @staticmethod
    async def get_customer_statistics(period: str, db: AsyncSession) -> CustomerStatisticsResponse:
        start = _period_start(period)
        query = select(func.count()).select_from(Buyer)
        if start is not None:
            query = query.where(Buyer.created_at >= start)
        try:
            count = await db.scalar(query)
            return CustomerStatisticsResponse(period=period, new_customers=count or 0)
        except SQLAlchemyError:
            raise HTTPException(status_code=500, detail="Unable to retrieve customer statistics")
