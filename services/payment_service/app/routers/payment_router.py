from app.controllers.payment_controller import PaymentProcessorController
from app.core.schemas import WalletCreate
from fastapi import APIRouter, Depends, Request
from app.db.session import get_db
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/api/v1/payment", tags=["payment"])

@router.post("/wallet")
async def create_user_wallet(req: Request, payload: WalletCreate, db: AsyncSession = Depends(get_db)):
    return await PaymentProcessorController.create_wallet(payload, db, req)