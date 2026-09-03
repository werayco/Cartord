from fastapi import HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.schemas import (ChangePasswordRequest, LoginRequest, RegisterRequest)
from app.models.buyer import Buyer
from app.models.outbox import OutboxEvent
from app.core.utils import get_tokens, hash_password, verify_password

class BuyerController:
    @staticmethod
    async def register(payload: RegisterRequest, db: AsyncSession):
        result = await db.execute(
            select(Buyer).where(
                or_(Buyer.email == payload.email, Buyer.username == payload.username)
            )
        )
        if result.scalars().first():
            return {"response": "this Buyer already exists", "status": "failed"}

        password_hash = hash_password(payload.password)
        buyer_data = Buyer(
            email=payload.email,
            username=payload.username,
            name=payload.name,
            password=password_hash,
            shipping_address=payload.shipping_address,
        )
        db.add(buyer_data)
        await db.flush()

        db.add(OutboxEvent(
            event_type="buyer.registered",
            aggregate_id=str(buyer_data.id),
            payload={"customer_id": str(buyer_data.id), "email": buyer_data.email},
        ))

        await db.commit()
        await db.refresh(buyer_data)
        tokens = await get_tokens(buyer_data)
        return {"response": "Registration successful", "tokens": tokens}

    @staticmethod
    async def login(payload: LoginRequest, db: AsyncSession):
        result = await db.execute(select(Buyer).where(Buyer.username == payload.username))
        buyer = result.scalar_one_or_none()
        if not buyer or not verify_password(payload.password, buyer.password):
            raise HTTPException(status_code=401, detail="Invalid username or password")
        tokens = await get_tokens(buyer)
        return {"response": "Login successful", "tokens": tokens}

    @staticmethod
    async def update_user(payload: RegisterRequest, db: AsyncSession, current_user: Buyer):
        update_data = payload.model_dump(exclude_unset=True, exclude={"password"})

        if "email" in update_data or "username" in update_data:
            result = await db.execute(
                select(Buyer).where(
                    or_(
                        Buyer.email == update_data.get("email", current_user.email),
                        Buyer.username == update_data.get("username", current_user.username),
                    ),
                    Buyer.id != current_user.id,
                )
            )
            if result.scalars().first():
                raise HTTPException(status.HTTP_409_CONFLICT, detail="Email or username already taken")

        for k, v in update_data.items():
            setattr(current_user, k, v)

        await db.commit()
        await db.refresh(current_user)
        return {"response": "Update successful"}

    @staticmethod
    async def delete_user(payload: LoginRequest, db: AsyncSession, current_user: Buyer):
        if not verify_password(payload.password, current_user.password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password is incorrect",
            )
        await db.delete(current_user)
        await db.commit()
        return {"response": "Account deleted successfully"}

    @staticmethod
    async def change_password(payload: ChangePasswordRequest, current_user: Buyer, db: AsyncSession):
        if not verify_password(payload.old_password, current_user.password):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Old password is incorrect")
        current_user.password = hash_password(payload.new_password)
        await db.commit()
        return {"response": "Password changed successfully"}