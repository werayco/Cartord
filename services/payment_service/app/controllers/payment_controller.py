from app.db.session import get_db
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.schemas import WalletCreate
from app.models.user_wallet import UserWallet
from app.core.config import settings
from fastapi import Request, status
from fastapi.exceptions import HTTPException
import secrets
from app.core.logging import logger

class PaymentProcessorController:
    @staticmethod
    async def create_wallet(payload: WalletCreate, db: AsyncSession, req: Request):
        incoming_key = req.headers.get("SHARED_API_KEY")
        print(f"incoming header key is {incoming_key}")
        logger.info(f"incoming header key is {incoming_key}")

        if not incoming_key or not secrets.compare_digest(
            incoming_key, settings.SERVICE_SHARED_KEY
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or missing shared API key",)

        try:
            result = UserWallet(user_id=payload.user_id)
            db.add(result)
            await db.commit()
            await db.refresh(result)
            return result
        except Exception as e:
            await db.rollback()
            raise e