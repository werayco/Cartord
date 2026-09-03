from app.controllers.payment_controller import PaymentProcessorController
from app.core.schemas import WalletCreate
from fastapi import APIRouter, Depends, Request
from app.db.session import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.utils import get_current_user
from app.core.schemas import WalletResponse

router = APIRouter(prefix="/api/v1/wallets", tags=["payment"])

@router.get("/seller", response_model=WalletResponse)
async def get_seller_wallet(db: AsyncSession = Depends(get_db), current_user = Depends(get_current_user)):
    return await PaymentProcessorController.get_seller_wallet(db, current_user)

@router.get("/buyer", response_model=WalletResponse)
async def get_buyer_wallet(db: AsyncSession = Depends(get_db), current_user = Depends(get_current_user)):
    return await PaymentProcessorController.get_buyer_wallet(db, current_user)