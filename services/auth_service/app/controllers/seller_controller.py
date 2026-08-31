from uuid import UUID
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from app.models import Seller
from app.core.config import settings
from app.core.schemas import LoginRequest, RegisterSeller, RegisterAdmin, Roles
from app.db.session import AsyncSessionLocal
from app.core.utils import hash_password, verify_password, get_tokens

class SellerController:
    @staticmethod
    async def register_admin(payload: RegisterAdmin, db: AsyncSession):
        result = await db.execute(
                select(Seller).where(
                    or_(
                        Seller.email == payload.email,
                        Seller.username == payload.username,
                    )
                )
            )
        if result.scalars().first():
            return {"message": "Admin already exists", "created": True}

        try:
            data = payload.model_dump()
            data["role"] = Roles.ADMIN
            data["password"] = hash_password(data["password"])

            admin_data = Seller(**data)
            db.add(admin_data)

            await db.commit()
            await db.refresh(admin_data)
            return {"message": "Admin registered successfully", "created": True}
        except Exception as e:
            await db.rollback()
            print("error --- ", str(e))
            return {"message": "Error during admin registration", "error": str(e), "created": False}

    @staticmethod
    async def register_seller(payload: RegisterSeller, db: AsyncSession):
        try:
            data = payload.model_dump()
            result = await db.execute(
                select(Seller).where(
                    or_(
                        Seller.email == payload.email,
                        Seller.username == payload.username,
                    )
                )
            )
            if result.scalars().first():
                raise HTTPException(status_code=409, detail="Username already exists")

            data["role"] = Roles.SELLER
            data["password"] = hash_password(data["password"])

            add_seller = Seller(**data)
            db.add(add_seller)
            await db.commit()
            await db.refresh(add_seller)
            return {"message": "Seller registered successfully"}
        except HTTPException:
            await db.rollback()
            raise
        except Exception as e:
            await db.rollback()
            raise HTTPException(status_code=500, detail=str(e))

    @staticmethod
    async def run():
        data = RegisterAdmin(email=settings.ADMIN_EMAIL, name=settings.ADMIN_NAME, password=settings.ADMIN_PASSWORD, username=settings.ADMIN_USERNAME)
        async with AsyncSessionLocal() as db:
            response = await SellerController.register_admin(payload=data, db=db)
            return "Admin Created" if response.get("created") else response["message"]

    @staticmethod
    async def get_all_sellers(db: AsyncSession, current_user: Seller):
        if current_user.role != Roles.ADMIN:
            raise HTTPException(status_code=403, detail="Only an admin can view sellers")
        result = await db.execute(select(Seller).where(Seller.role == Roles.SELLER))
        return result.scalars().all()

    @staticmethod
    async def delete_user(username: str, db: AsyncSession, current_user: Seller):
        if username == current_user.username:
            raise HTTPException(status_code=400, detail="Admins cannot delete their own account")

        result = await db.execute(select(Seller).where(Seller.username == username))
        seller = result.scalars().first()
        if not seller:
            raise HTTPException(status_code=404, detail="User not found")

        if seller.role == Roles.ADMIN:
            raise HTTPException(status_code=403, detail="Cannot delete an admin account")

        try:
            await db.delete(seller)
            await db.commit()
            return {"message": "User deleted successfully"}
        except Exception as e:
            await db.rollback()
            raise HTTPException(status_code=500, detail=str(e))

    @staticmethod
    async def login(payload: LoginRequest, db: AsyncSession):
        result = await db.execute(select(Seller).where(Seller.username == payload.username))
        seller = result.scalar_one_or_none()
        if not seller or not verify_password(payload.password, seller.password):
            raise HTTPException(status_code=401, detail="Invalid username or password")
        tokens = await get_tokens(seller)
        return {"response": "Login successful", "tokens": tokens}