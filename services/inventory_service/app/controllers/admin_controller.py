from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.schemas import InventoryAdminItem, InventorySummaryResponse
from app.models.product import Inventory


class AdminController:
    @staticmethod
    async def get_low_stock(db: AsyncSession) -> list[InventoryAdminItem]:
        return await AdminController._stock_query(db, out_of_stock=False)

    @staticmethod
    async def get_out_of_stock(db: AsyncSession) -> list[InventoryAdminItem]:
        return await AdminController._stock_query(db, out_of_stock=True)

    @staticmethod
    async def _stock_query(db: AsyncSession, out_of_stock: bool) -> list[InventoryAdminItem]:
        try:
            result = await db.execute(select(Inventory).where(Inventory.is_active.is_(True)))
            records = result.scalars().all()
            threshold = settings.LOW_STOCK_THRESHOLD
            filtered = []
            for record in records:
                sellable_quantity = record.available_quantity - record.reserved_quantity
                if (out_of_stock and sellable_quantity <= 0) or (not out_of_stock and 0 < sellable_quantity <= threshold):
                    filtered.append(InventoryAdminItem(
                        name=record.name, sku=record.sku, unit_price=record.unit_price,
                        available_quantity=record.available_quantity, created_at=record.created_at,
                        description=record.description, reserved_quantity=record.reserved_quantity,
                        sellable_quantity=sellable_quantity,
                    ))
            return filtered
        except SQLAlchemyError:
            raise HTTPException(status_code=500, detail="Unable to retrieve inventory stock report")

    @staticmethod
    async def get_summary(db: AsyncSession) -> InventorySummaryResponse:
        try:
            result = await db.execute(select(Inventory).where(Inventory.is_active.is_(True)))
            records = result.scalars().all()
            return InventorySummaryResponse(
                total_skus=len(records),
                total_units=sum(record.available_quantity for record in records),
                total_inventory_value=round(sum(Decimal(record.available_quantity) * record.unit_price for record in records), 2),
            )
        except SQLAlchemyError:
            raise HTTPException(status_code=500, detail="Unable to retrieve inventory summary")