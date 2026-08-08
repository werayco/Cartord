from functools import partial
from typing import Any
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.order import Order
from app.models.outbox import OutboxEvent
from app.schemas import OrderPayload
from app.services.idempotency import idempotency
from app.utils import update_inventory

class OrderController:
    @staticmethod
    async def place_order(payload: OrderPayload, current_user: dict[str, Any], db: AsyncSession, idempotency_key: str):
        user_id = current_user.get("id")
        operation = partial(OrderController.create_order, payload, str(user_id), db)

        result = await idempotency(idempotency_key=idempotency_key, user_id=str(user_id), operation=operation)
        if result["status"] == "processing": raise HTTPException(status_code=409, detail=result["message"])
        return result["result"]

    @staticmethod
    async def create_order(payload: OrderPayload, user_id: str, db: AsyncSession):
        inventory_reserved = False
        try:
            reservation = await update_inventory(sku=payload.sku, reserved_quantity=payload.quantity)
            if reservation.get("status") != "successful": raise HTTPException(status_code=409, detail="Unable to reserve inventory for this order")
            inventory_reserved = True

            order_entry = Order(sku=payload.sku, unit_price=reservation.get("unit_price"), customer_id=user_id, quantity=payload.quantity)
            db.add(order_entry)

            await db.flush()

            outbox_event = OutboxEvent(event_type="order.created", aggregate_id=str(order_entry.id), payload={"order_id": str(order_entry.id), "sku": order_entry.sku, "quantity": order_entry.quantity, "customer_id": str(order_entry.customer_id)})
            db.add(outbox_event)

            await db.commit()
            await db.refresh(order_entry)
            return {"order_id": str(order_entry.id), "sku": order_entry.sku, "quantity": order_entry.quantity, "customer_id": str(order_entry.customer_id), "unit_price": order_entry.unit_price, "status": "created"}
        except HTTPException:
            await db.rollback()
            if inventory_reserved: await update_inventory(sku=payload.sku, reserved_quantity=-payload.quantity)
            raise
        except Exception:
            await db.rollback()
            if inventory_reserved: await update_inventory(sku=payload.sku, reserved_quantity=-payload.quantity)
            raise HTTPException(status_code=500, detail="Failed to create order")

    @staticmethod
    async def cancel_order(payload: OrderPayload, user: dict[str, Any], db: AsyncSession):
        ...