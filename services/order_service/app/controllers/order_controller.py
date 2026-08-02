from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas import *
from app.kafka.producer import kafka_manager as producer
from app.utils import seralize_to_json, update_inventory
from app.models.order import Order

class OrderController:
    @staticmethod
    async def place_order(payload: OrderPayload, current_user: dict, db: AsyncSession):
        try:
            reservation = await update_inventory(sku=payload.sku, reserved_quantity=payload.quantity)
            if reservation.get("status") != "successful":
                raise HTTPException(status_code=409, detail="Unable to reserve inventory for this order")
            
            order_entry = Order(
                sku=payload.sku,
                unit_price=reservation.get("unit_price"),
                customer_id=current_user.get("id"),
                quantity=payload.quantity,
            )
            db.add(order_entry)
            await db.commit()
            await db.refresh(order_entry)
        except Exception:
            await update_inventory(sku=payload.sku, reserved_quantity=-payload.quantity)
            await db.rollback()
            raise HTTPException(status_code=500, detail="Failed to create order, inventory reservation rolled back")

        try:
            await producer.produce(
                key="order.created",
                value=seralize_to_json({
                    "order_id": str(order_entry.id),
                    "sku": order_entry.sku,
                    "quantity": order_entry.quantity,
                    "customer_id": str(order_entry.customer_id),
                }),
            )
        except Exception:
            print(f"Failed to publish order.created for order {order_entry.id}")
        return order_entry

    @staticmethod
    async def cancel_order(payload:OrderPayload, user, db:AsyncSession):
        ...