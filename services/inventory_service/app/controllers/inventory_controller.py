from sqlalchemy import select, inspect
from fastapi import HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas import *
from app.kafka.producer import kafka_manager
from app.models import Inventory, Employee
from app.config import settings
from app.utils import seralize_to_json

ALLOW_ROLES = (Roles.ADMIN, Roles.INVENTORY_MANAGER)


class InventoryCRUD:
    @staticmethod
    async def add_inventory_item(db: AsyncSession, inventory: InventorySchema, current_user: Employee):
        if current_user.role not in ALLOW_ROLES:
            raise HTTPException(status_code=403, detail="You do not have the necessary permission to add a product. Contact your admin or inventory manager.")

        try:
            payload = inventory.model_dump()
            record = Inventory(**payload)

            db.add(record)
            await db.commit()
            await db.refresh(record)

            payload["id"] = record.id

            kafka_manager.produce(topic="inventory", key="inventory.created", value=seralize_to_json(payload))
            return {"message": "Inventory item added successfully"}

        except Exception as e:
            await db.rollback()
            raise HTTPException(status_code=500, detail=str(e))

    @staticmethod
    async def add_inventory_items(db: AsyncSession, inventory: InventorySchemaList, current_user: Employee):
        if current_user.role not in ALLOW_ROLES:
            raise HTTPException(status_code=403, detail="You do not have the necessary permission to add a product. Contact your admin or inventory manager.")

        try:
            payloads: list = inventory.model_dump()
            records = [Inventory(**item) for item in payloads]

            db.add_all(records)
            await db.commit()

            for item_dict, db_record in zip(payloads, records):
                item_dict["id"] = db_record.id

                kafka_manager.produce(topic="inventory", key="inventory.created", value=seralize_to_json(item_dict))
            return {"message": "Inventory items added successfully"}

        except Exception as e:
            await db.rollback()
            raise HTTPException(status_code=500, detail=str(e))

    @staticmethod
    async def delete_inventory_item(db: AsyncSession, inventory: InventorySchema, current_user: Employee):
        if current_user.role not in ALLOW_ROLES:
            raise HTTPException(status_code=403, detail="You do not have the necessary permission to delete a product from the inventory, contact your admin or inventory manager")

        result = (await db.execute(select(Inventory).where(Inventory.sku == inventory.sku)))
        record = result.scalar_one_or_none()

        if not record:
            raise HTTPException(status_code=404, detail="Inventory item not found")

        try:
            record_dict = {col.key: getattr(record, col.key) for col in inspect(record).mapper.column_attrs}

            await db.delete(record)
            await db.commit()

            kafka_manager.produce(topic="inventory", key="inventory.deleted", value=seralize_to_json(record_dict))
            return {"message": "Inventory item deleted successfully"}
        except Exception as e:
            await db.rollback()
            raise HTTPException(status_code=500, detail=str(e))

    @staticmethod
    async def update_inventory_item(db: AsyncSession, inventory: InventorySchema, current_user: Employee):
        if current_user.role not in ALLOW_ROLES:
            raise HTTPException(status_code=403, detail="You do not have the necessary permission to update the inventory, contact your admin or inventory manager")

        result = (await db.execute(select(Inventory).where(Inventory.sku == inventory.sku)))
        record = result.scalar_one_or_none()
        if not record:
            raise HTTPException(status_code=404, detail="Inventory item not found")

        try:
            for key, value in inventory.model_dump().items():
                setattr(record, key, value)

            await db.commit()
            await db.refresh(record)

            kafka_manager.produce(topic="inventory", key="inventory.updated", value=seralize_to_json(inventory.model_dump()))
            return {"message": "Inventory item updated successfully"}

        except Exception as e:
            await db.rollback()
            raise HTTPException(status_code=500, detail=str(e))


    @staticmethod
    async def reserve_inventory(inventory:InventoryReserve, req: Request, db: AsyncSession):
        shared_api_key = req.headers.get("SHARED_API_KEY")

        if not shared_api_key:
            raise HTTPException(status_code=403, detail="Insert the service shared key as a request header")
        
        if shared_api_key != settings.SERVICE_SHARED_KEY:
            raise HTTPException(status_code=402, detail="Not authorized")

        result = (await db.execute(select(Inventory).where(Inventory.sku == inventory.sku)))
        record = result.scalar_one_or_none()

        if not record:
            raise HTTPException(status_code=404, detail="Inventory item not found")
        
        try:
            record.reserved_quantity += inventory.reserved_quantity
            await db.commit()
            await db.refresh(record)

            return {"message": f"{inventory.reserved_quantity} pieces of {inventory.sku} has been reserved", "status": "successful", "unit_price": record.unit_price}

        except Exception as e:
            await db.rollback()
            raise HTTPException(status_code=500, detail=str(e))

    @staticmethod
    async def get_inventory_item(db: AsyncSession, inventory: InventorySchema, current_user: Employee):
        result = (await db.execute(select(Inventory).where(Inventory.sku == inventory.sku)))
        record = result.scalar_one_or_none()
        if not record:
            raise HTTPException(status_code=404, detail="Inventory item not found")
        return record