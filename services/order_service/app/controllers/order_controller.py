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
        user_details = await get_user_details(access_token)
        update_inventory = update_inventory()

        # update the inventory -- increase the reserved_amount by the quantity the user wants
        # after, insert a order entry into the order table,
        ... # i am going to update the Order Table with the user detail and then publish a order.creeated into the order topic, then increase the reserved_amount in the inventory service
    @staticmethod
    async def cancel_order(payload:OrderPayload, user, db:AsyncSession):
        ...