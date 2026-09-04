from functools import partial
from typing import Any
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.order import Order
from app.models.outbox import OutboxEvent
from app.core.schemas import OrderPayload
from app.services.idempotency import idempotency
import aiohttp
from app.core.utils import update_inventory
from uuid import UUID
from app.core.schemas import OrderStatus
from app.core.logging import logger

class OrderController:
    @staticmethod
    async def place_order(payload: OrderPayload, current_user: dict[str, Any], db: AsyncSession, idempotency_key: str):
        user_id = current_user.get("id")
        email = current_user.get("email")
        operation = partial(OrderController.create_order, payload, str(user_id), email, db)
        logger.info(f"Placing order for user_id: {user_id} with idempotency_key: {idempotency_key}")
        result = await idempotency(idempotency_key=idempotency_key, user_id=str(user_id), operation=operation)
        if result["status"] == "processing":
            raise HTTPException(status_code=409, detail=result["message"])
        return result["result"]

    @staticmethod
    async def create_order(payload: OrderPayload, user_id: str, email: str, db: AsyncSession):
        inventory_reserved = False
        try:
            reservation = await update_inventory(sku=payload.sku, reserved_quantity=payload.quantity)
            logger.info(f"Inventory reservation response for SKU {payload.sku}: {reservation}")
            if reservation.get("status") != "successful":
                raise HTTPException(status_code=409, detail="Unable to reserve inventory for this order")
            inventory_reserved = True
            logger.info(f"Creating order entry for user_id: {user_id}, SKU: {payload.sku}, quantity: {payload.quantity}")
            order_entry = Order(sku=payload.sku, unit_price=reservation.get("unit_price"), customer_id=user_id, quantity=payload.quantity, seller_id=reservation.get("seller_id"))
            db.add(order_entry)

            await db.flush()
            event_payload = {
                    "order_id": str(order_entry.id),
                    "sku": order_entry.sku,
                    "quantity": order_entry.quantity,
                    "customer_id": str(order_entry.customer_id),
                    "unit_price": float(order_entry.unit_price),
                    "email": email,
                    "seller_id": str(order_entry.seller_id) if order_entry.seller_id else None,
                }
            logger.info(f"Creating outbox event for order_id: {order_entry.id} with payload: {event_payload}")
            outbox_event = OutboxEvent(
                event_type="order.created",
                aggregate_id=str(order_entry.id),
                payload=event_payload,
            )
            db.add(outbox_event)

            await db.commit()
            await db.refresh(order_entry)
            logger.info(f"Order created successfully with order_id: {order_entry.id}")
            return {
                "order_id": str(order_entry.id),
                "sku": order_entry.sku,
                "quantity": order_entry.quantity,
                "customer_id": str(order_entry.customer_id),
                "unit_price": float(order_entry.unit_price),
                "seller_id": str(order_entry.seller_id) if order_entry.seller_id else None,
                "status": "created",
            }
        except aiohttp.ClientResponseError as e:
            await db.rollback()
            if inventory_reserved:
                logger.info(f"Releasing inventory reservation for SKU {payload.sku} due to error: {e}")
                await update_inventory(sku=payload.sku, reserved_quantity=-payload.quantity)
            raise HTTPException(status_code=e.status, detail=e.message)
        except HTTPException:
            await db.rollback()
            if inventory_reserved:
                await update_inventory(sku=payload.sku, reserved_quantity=-payload.quantity)
            raise
        except Exception as e:
            await db.rollback()
            if inventory_reserved:
                logger.info(f"Releasing inventory reservation for SKU {payload.sku} due to unexpected error: {e}")
                await update_inventory(sku=payload.sku, reserved_quantity=-payload.quantity)
            raise HTTPException(status_code=500, detail="Failed to create order")

    @staticmethod
    async def confirm_order(payment_event: dict, db: AsyncSession):
        order_id = payment_event.get("order_id")
        if not order_id:
            logger.error(f"Malformed payment event, missing order_id: {payment_event}")
            return

        order = await db.get(Order, UUID(order_id))
        if not order:
            logger.error(f"Received payment.succeeded for unknown order {order_id}")
            return
        if order.status != OrderStatus.PENDING:
            logger.info(f"Order {order_id} already in status {order.status}, skipping")
            return

        order.status = OrderStatus.CONFIRMED
        await db.commit()

    @staticmethod
    async def fail_order(payment_event: dict, db: AsyncSession):
        order_id = payment_event.get("order_id")
        if not order_id:
            logger.error(f"Malformed failure event, missing order_id: {payment_event}")
            return

        order = await db.get(Order, UUID(order_id))
        if not order:
            logger.error(f"Received failure event for unknown order {order_id}")
            return
        if order.status != OrderStatus.PENDING:
            logger.info(f"Order {order_id} already in status {order.status}, skipping")
            return

        order.status = OrderStatus.CANCELLED
        await db.commit()

        try:
            await update_inventory(sku=order.sku, reserved_quantity=-order.quantity)
        except Exception as e:
            logger.critical(f"Order {order_id} cancelled but failed to release inventory reservation: {e}")