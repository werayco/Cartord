from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas import (RefreshRequest,ChangePasswordRequest,LoginRequest,RegisterRequest, DeleteUser, CustomerOut)
from app.db.session import get_db
from app.models.customer import Customer
from app.utils import (get_current_user_dep,cache_refresh_tokens)
from app.controllers.customer_controller import AuthController

user_router = APIRouter(prefix="/api/v1/auth/user", tags=["auth"])

@user_router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(payload: RegisterRequest, db: AsyncSession = Depends(get_db)):
    return await AuthController.register(payload, db)

@user_router.post("/login")
async def login(payload: LoginRequest, db: AsyncSession = Depends(get_db)):
    return await AuthController.login(payload, db)

@user_router.post("/refresh")
async def refresh(refresh_token:RefreshRequest, current_user: Customer = Depends(get_current_user_dep(Customer))):
    tokens = await cache_refresh_tokens(current_user.id,refresh_token)
    return tokens

@user_router.get("/me", response_model=CustomerOut)
async def me(current_user: Customer = Depends(get_current_user_dep(Customer))):
    return current_user

@user_router.post("/change-password")
async def change_password(payload: ChangePasswordRequest,current_user: Customer = Depends(get_current_user_dep(Customer)),db: AsyncSession = Depends(get_db),):
    return await AuthController.change_password(payload, current_user, db)

@user_router.patch("/update")
async def update_user(payload: RegisterRequest, current_user: Customer = Depends(get_current_user_dep(Customer)),db: AsyncSession = Depends(get_db),):
    return await AuthController.update_user(payload, db, current_user)

@user_router.delete("/delete")
async def delete_user(payload: DeleteUser, current_user: Customer = Depends(get_current_user_dep(Customer)),db: AsyncSession = Depends(get_db),):
    return await AuthController.delete_user(payload, db, current_user)