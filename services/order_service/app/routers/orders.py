from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.controllers.order_controller import OrderController
from app.core.schemas import OrderPayload, OrderResponse
from app.core.utils import get_current_user
from app.db.session import get_db

order_router = APIRouter(prefix="/api/v1/order", tags=["order"])


@order_router.post("/place/{idempotency_key}", response_model=list[OrderResponse])
async def place_order(
    payload: list[OrderPayload],
    idempotency_key: str,
    current_user: dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await OrderController.place_order(payload, current_user, db, idempotency_key)


@order_router.get("/summary")
async def get_order_summary(
    current_user=Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    return await OrderController.get_summary(current_user, db)
