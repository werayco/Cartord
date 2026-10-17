import secrets

from fastapi import HTTPException, Request, status
from sqlalchemy import inspect, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import generate_skus, logger, settings, to_json_safe
from app.core.schemas import *
from app.models import Inventory, OutboxEvent

ALLOW_ROLES = (Roles.ADMIN.value, Roles.SELLER.value)


class InventoryCRUD:
    @staticmethod
    async def add_inventory_item(
        db: AsyncSession, inventory: InventorySchema, current_user: dict
    ):
        if current_user.get("role") not in ALLOW_ROLES:
            raise HTTPException(
                status_code=403,
                detail="You do not have the necessary permission to add a product. Contact your admin or inventory manager.",
            )

        try:
            payload = inventory.model_dump()
            payload["seller_id"] = current_user.get("id")
            (sku,) = await generate_skus(db, 1)
            payload["sku"] = sku
            record = Inventory(**payload)

            db.add(record)
            await db.flush()

            payload["id"] = record.id
            db.add(
                OutboxEvent(
                    event_type="inventory.created",
                    aggregate_id=str(record.id),
                    payload=payload,
                )
            )

            await db.commit()
            await db.refresh(record)
            return {"message": "Inventory item added successfully", "sku": sku}

        except Exception as e:
            await db.rollback()
            raise HTTPException(status_code=500, detail=str(e))

    @staticmethod
    async def add_inventory_items(
        db: AsyncSession, inventory: InventorySchemaList, current_user: dict
    ):
        if current_user.get("role") not in ALLOW_ROLES:
            raise HTTPException(
                status_code=403,
                detail="You do not have the necessary permission to add a product. Contact your admin or inventory manager.",
            )

        try:
            payloads: list = inventory.model_dump()
            skus = await generate_skus(db, len(payloads))
            for item, sku in zip(payloads, skus):
                item["seller_id"] = current_user.get("id")
                item["sku"] = sku
            records = [Inventory(**item) for item in payloads]

            db.add_all(records)
            await db.flush()

            for item_dict, db_record in zip(payloads, records):
                item_dict["id"] = db_record.id
                db.add(
                    OutboxEvent(
                        event_type="inventory.created",
                        aggregate_id=str(db_record.id),
                        payload=item_dict,
                    )
                )

            await db.commit()
            return {"message": "Inventory items added successfully", "skus": skus}

        except Exception as e:
            await db.rollback()
            raise HTTPException(status_code=500, detail=str(e))

    @staticmethod
    async def delete_inventory_item(
        db: AsyncSession,
        inventory: InventorySchema,
        current_user: dict,
    ):
        role = current_user.get("role")
        user_id = current_user.get("id")

        if role not in ALLOW_ROLES:
            raise HTTPException(
                status_code=403,
                detail="Permission denied.",
            )

        result = await db.execute(
            select(Inventory).where(Inventory.sku == inventory.sku)
        )
        record = result.scalar_one_or_none()

        if not record:
            raise HTTPException(
                status_code=404,
                detail="Inventory item not found",
            )

        if role == Roles.SELLER.value and record.seller_id != user_id:
            raise HTTPException(
                status_code=403,
                detail="Permission denied.",
            )

        try:
            record_dict = {
                col.key: getattr(record, col.key)
                for col in inspect(record).mapper.column_attrs
            }

            db.add(
                OutboxEvent(
                    event_type="inventory.deleted",
                    aggregate_id=str(record.id),
                    payload=to_json_safe(record_dict),
                )
            )

            await db.delete(record)
            await db.commit()

            return {"message": "Inventory item deleted successfully"}

        except Exception as e:
            await db.rollback()
            logger.exception("Inventory deletion failed")
            raise HTTPException(
                status_code=500,
                detail="Failed to delete inventory item",
            ) from e

    @staticmethod
    async def update_inventory_item(
        db: AsyncSession,
        inventory: InventorySchema,
        current_user: dict,
    ):
        role = current_user.get("role")
        user_id = current_user.get("id")

        if role not in ALLOW_ROLES:
            raise HTTPException(
                status_code=403,
                detail="Permission denied.",
            )

        result = await db.execute(
            select(Inventory).where(Inventory.sku == inventory.sku)
        )
        record = result.scalar_one_or_none()

        if not record:
            raise HTTPException(
                status_code=404,
                detail="Inventory item not found",
            )

        if role == Roles.SELLER.value and record.seller_id != user_id:
            raise HTTPException(
                status_code=403,
                detail="Permission denied.",
            )

        try:
            update_data = inventory.model_dump(exclude_unset=True)

            update_data.pop("sku", None)
            update_data.pop("seller_id", None)
            update_data.pop("id", None)

            for key, value in update_data.items():
                setattr(record, key, value)

            await db.flush()

            payload = {
                col.key: getattr(record, col.key)
                for col in inspect(record).mapper.column_attrs
            }

            db.add(
                OutboxEvent(
                    event_type="inventory.updated",
                    aggregate_id=str(record.id),
                    payload=to_json_safe(payload),
                )
            )

            await db.commit()
            await db.refresh(record)

            return {"message": "Inventory item updated successfully"}

        except Exception as e:
            await db.rollback()
            logger.exception("Inventory update failed")
            raise HTTPException(
                status_code=500,
                detail="Failed to update inventory item",
            ) from e

    @staticmethod
    async def reserve_inventory(
        inventory: InventoryReserve, req: Request, db: AsyncSession
    ):
        incoming_key = req.headers.get("SHARED_API_KEY")
        if not incoming_key or not secrets.compare_digest(
            incoming_key, settings.SERVICE_SHARED_KEY
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or missing shared API key",
            )

        result = await db.execute(
            select(Inventory).where(Inventory.sku == inventory.sku)
        )
        record = result.scalar_one_or_none()

        if not record:
            raise HTTPException(status_code=404, detail="Inventory item not found")

        free = record.available_quantity - record.reserved_quantity
        if free < inventory.reserved_quantity:
            raise HTTPException(
                status_code=409,
                detail=f"Insufficient stock for SKU {inventory.sku}: available {free}, requested {inventory.reserved_quantity}",
            )

        try:
            record.reserved_quantity += inventory.reserved_quantity
            await db.commit()
            await db.refresh(record)
            return {
                "message": "Inventory reserved successfully",
                "remaining_quantity": record.available_quantity
                - record.reserved_quantity,
                "status": "successful",
                "unit_price": record.unit_price,
                "seller_id": record.seller_id,
            }
        except Exception as e:
            await db.rollback()
            raise HTTPException(status_code=500, detail=str(e))

    @staticmethod
    async def get_inventory_item(db: AsyncSession, current_user: dict):
        query = select(Inventory)
        if current_user.get("role") == Roles.SELLER.value:
            seller_id = current_user.get("id")
            if not seller_id:
                raise HTTPException(status_code=403, detail="Seller identity is missing")
            query = query.where(Inventory.seller_id == seller_id)

        result = await db.execute(query)
        records = result.scalars().all()
        return records
