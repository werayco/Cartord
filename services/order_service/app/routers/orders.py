from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.utils import get_current_user
from app.schemas import OrderPayload
from app.controllers.order_controller import OrderController

order_router = APIRouter(prefix="/api/v1/order",tags=["order"])

@order_router.post("/place")
async def place_order(payload: OrderPayload, current_user: str = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return await OrderController.place_order(payload, current_user, db)