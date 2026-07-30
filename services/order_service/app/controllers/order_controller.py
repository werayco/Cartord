from sqlalchemy import select
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas import *
from app.kafka.producer import kafka_manager
from app.utils import get_user_details, seralize_to_json, update_inventory
from app.models.order import Order

class OrderController:
    @staticmethod
    async def place_order(payload: OrderPayload, access_token, db: AsyncSession):
        try:
            user_details: dict = await get_user_details(access_token)
            update_invent = await update_inventory(sku=payload.sku, reserved_quantity=payload.quantity)
            if update_invent.get("status") == "successful":
                order_entry = Order(sku=payload.sku, unit_price=payload.price, customer_id=user_details.get("id"),quantity=payload.quantity )
                await db.add(order_entry)
                await db.commit()

            # update the inventory -- increase the reserved_amount by the quantity the user wants
            # after, insert a order entry into the order table,
            ... # i am going to update the Order Table with the user detail and then publish a order.creeated into the order topic, then increase the reserved_amount in the inventory service
        except:
            ...

    @staticmethod
    async def cancel_order(payload:OrderPayload, user, db:AsyncSession):
        ...