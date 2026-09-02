from datetime import datetime, timedelta, timezone
from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.schemas import FailedOrderStatisticsResponse, OrderStatisticsResponse, OrderStatus
from app.models.order import Order

_PERIODS = {"day": timedelta(days=1), "week": timedelta(weeks=1), "month": timedelta(days=30), "year": timedelta(days=365)}

def _period_start(period: str) -> datetime | None:
    if period == "all":
        return None
    duration = _PERIODS.get(period)
    if duration is None:
        raise HTTPException(status_code=422, detail="period must be one of: day, week, month, year, all")
    return datetime.now(timezone.utc) - duration


def _period_filter(query, period: str):
    start = _period_start(period)
    return query.where(Order.created_at >= start) if start is not None else query

class AdminController:
    @staticmethod
    async def get_order_statistics(period: str, db: AsyncSession) -> OrderStatisticsResponse:
        try:
            query = _period_filter(select(Order), period)
            orders = (await db.execute(query)).scalars().all()
            revenue = sum(float(order.unit_price) * order.quantity for order in orders)
            by_status = {}
            for order in orders:
                status = order.status.value if hasattr(order.status, "value") else str(order.status)
                by_status[status] = by_status.get(status, 0) + 1
            return OrderStatisticsResponse(
                period=period,
                total_orders=len(orders),
                total_items=sum(order.quantity for order in orders),
                total_revenue=round(revenue, 2),
                average_order_value=round(revenue / len(orders), 2) if orders else 0,
                orders_by_status=by_status,
            )
        except SQLAlchemyError:
            raise HTTPException(status_code=500, detail="Unable to retrieve order statistics")

    @staticmethod
    async def get_failed_order_statistics(period: str, db: AsyncSession) -> FailedOrderStatisticsResponse:
        try:
            query = _period_filter(select(Order).where(Order.status == OrderStatus.CANCELLED), period)
            orders = (await db.execute(query)).scalars().all()
            return FailedOrderStatisticsResponse(
                period=period,
                failed_orders=len(orders),
                failed_items=sum(order.quantity for order in orders),
                failed_revenue=round(sum(float(order.unit_price) * order.quantity for order in orders), 2),
            )
        except SQLAlchemyError:
            raise HTTPException(status_code=500, detail="Unable to retrieve failed order statistics")
