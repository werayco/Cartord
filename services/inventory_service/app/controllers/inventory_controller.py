from sqlalchemy import select, inspect, update
from fastapi import HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.schemas import *
from app.models import Inventory, OutboxEvent
from app.core.config import settings
from app.core.utils import to_json_safe

ALLOW_ROLES = (Roles.ADMIN.value, Roles.INVENTORY_MANAGER.value)

class InventoryCRUD:
    @staticmethod
    async def add_inventory_item(db: AsyncSession, inventory: InventorySchema, current_user: dict):
        if current_user.get("role") not in ALLOW_ROLES:
            raise HTTPException(status_code=403, detail="You do not have the necessary permission to add a product. Contact your admin or inventory manager.")

        try:
            payload = inventory.model_dump()
            record = Inventory(**payload)

            db.add(record)
            await db.flush()  # assigns record.id without committing yet

            payload["id"] = record.id
            db.add(OutboxEvent(event_type="inventory.created", aggregate_id=str(record.id), payload=payload))

            await db.commit()
            await db.refresh(record)
            return {"message": "Inventory item added successfully"}

        except Exception as e:
            await db.rollback()
            raise HTTPException(status_code=500, detail=str(e))

    @staticmethod
    async def add_inventory_items(db: AsyncSession, inventory: InventorySchemaList, current_user:dict):
        if current_user.get("role") not in ALLOW_ROLES:
            raise HTTPException(status_code=403, detail="You do not have the necessary permission to add a product. Contact your admin or inventory manager.")

        try:
            payloads: list = inventory.model_dump()
            records = [Inventory(**item) for item in payloads]

            db.add_all(records)
            await db.flush()

            for item_dict, db_record in zip(payloads, records):
                item_dict["id"] = db_record.id
                db.add(OutboxEvent(event_type="inventory.created", aggregate_id=str(db_record.id), payload=item_dict))

            await db.commit()
            return {"message": "Inventory items added successfully"}

        except Exception as e:
            await db.rollback()
            raise HTTPException(status_code=500, detail=str(e))

    @staticmethod
    async def delete_inventory_item(db: AsyncSession, inventory: InventorySchema, current_user:dict):
        if current_user.get("role") not in ALLOW_ROLES:
            raise HTTPException(status_code=403, detail="You do not have the necessary permission to delete a product from the inventory, contact your admin or inventory manager")

        result = (await db.execute(select(Inventory).where(Inventory.sku == inventory.sku)))
        record = result.scalar_one_or_none()

        if not record:
            raise HTTPException(status_code=404, detail="Inventory item not found")

        try:
            record_dict = {col.key: getattr(record, col.key) for col in inspect(record).mapper.column_attrs}

            db.add(OutboxEvent(event_type="inventory.deleted", aggregate_id=str(record.id), payload=to_json_safe(record_dict)))

            await db.delete(record)
            await db.commit()
            return {"message": "Inventory item deleted successfully"}
        except Exception as e:
            await db.rollback()
            raise HTTPException(status_code=500, detail=str(e))

    @staticmethod
    async def update_inventory_item(db: AsyncSession, inventory: InventorySchema, current_user:dict):
        if current_user.get("role") not in ALLOW_ROLES:
            raise HTTPException(status_code=403, detail="You do not have the necessary permission to update the inventory, contact your admin or inventory manager")

        result = (await db.execute(select(Inventory).where(Inventory.sku == inventory.sku)))
        record = result.scalar_one_or_none()
        if not record:
            raise HTTPException(status_code=404, detail="Inventory item not found")

        try:
            for key, value in inventory.model_dump().items():
                setattr(record, key, value)

            payload = inventory.model_dump()
            payload["id"] = record.id  # was missing before — ES "update" branch needs this
            db.add(OutboxEvent(event_type="inventory.updated", aggregate_id=str(record.id), payload=payload))

            await db.commit()
            await db.refresh(record)
            return {"message": "Inventory item updated successfully"}

        except Exception as e:
            await db.rollback()
            raise HTTPException(status_code=500, detail=str(e))