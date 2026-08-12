from fastapi import HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.schemas import (ChangePasswordRequest, LoginRequest, RegisterRequest)
from app.models.customer import Customer
from app.core.utils import (get_tokens, hash_password, verify_password)


class AuthController:
    @staticmethod
    async def register(payload: RegisterRequest, db: AsyncSession):
        result = await db.execute(
            select(Customer).where(
                or_(Customer.email == payload.email, Customer.username == payload.username)
            )
        )
        if result.scalars().first():
            return {"response": "this Customer already exists", "status": "failed"}

        password_hash = hash_password(payload.password)
        customer_data = Customer(
            email=payload.email,
            username=payload.username,
            name=payload.name,
            password=password_hash,
            shipping_address=payload.shipping_address,
        )
        db.add(customer_data)

        await db.commit()
        await db.refresh(customer_data)
        tokens = await get_tokens(customer_data)
        return {"response": "Registration successful", "tokens": tokens}

    @staticmethod
    async def login(payload: LoginRequest, db: AsyncSession):
        result = await db.execute(select(Customer).where(Customer.username == payload.username))
        customer = result.scalar_one_or_none()
        if not customer or not verify_password(payload.password, customer.password):
            raise HTTPException(status_code=401, detail="Invalid username or password")
        tokens = await get_tokens(customer)
        return {"response": "Login successful", "tokens": tokens}

    @staticmethod
    async def update_user(payload: RegisterRequest, db: AsyncSession, current_user: Customer):
        update_data = payload.model_dump(exclude_unset=True, exclude={"password"})

        if "email" in update_data or "username" in update_data:
            result = await db.execute(
                select(Customer).where(
                    or_(
                        Customer.email == update_data.get("email", current_user.email),
                        Customer.username == update_data.get("username", current_user.username),
                    ),
                    Customer.id != current_user.id,
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
    async def delete_user(payload: LoginRequest, db: AsyncSession, current_user: Customer):
        if not verify_password(payload.password, current_user.password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password is incorrect",
            )
        await db.delete(current_user)
        await db.commit()
        return {"response": "Account deleted successfully"}

    @staticmethod
    async def change_password(payload: ChangePasswordRequest, current_user: Customer, db: AsyncSession):
        if not verify_password(payload.old_password, current_user.password):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Old password is incorrect")
        current_user.password = hash_password(payload.new_password)
        await db.commit()
        return {"response": "Password changed successfully"}