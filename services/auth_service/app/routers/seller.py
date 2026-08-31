from uuid import UUID
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from uuid6 import UUID
from app.core.config import *
from app.db.session import get_db
from app.models.seller import Seller
from app.core.utils import (get_current_user_dep, get_tokens, cache_refresh_tokens)
from app.controllers.seller_controller import SellerController
from app.controllers.buyer_controller import BuyerController
from app.core.schemas import *

seller_router = APIRouter(prefix="/api/v1/auth/seller", tags=["auth"])

@seller_router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(payload: RegisterSeller, db: AsyncSession = Depends(get_db)):
    return await SellerController.register_seller(payload, db)

@seller_router.delete("/{username}", status_code=status.HTTP_201_CREATED)
async def delete_user(username: str, db: AsyncSession = Depends(get_db), current_user: Seller = Depends(get_current_user_dep(Seller))):
    return await SellerController.delete_user(username, db, current_user)

@seller_router.get("/sellers", status_code=status.HTTP_201_CREATED, response_model=list[SellerOut])
async def get_all_sellers(db: AsyncSession = Depends(get_db), current_user: Seller = Depends(get_current_user_dep(Seller))):
    return await SellerController.get_all_sellers(db, current_user)

@seller_router.post("/login")
async def login(payload: LoginRequest, db: AsyncSession = Depends(get_db)):
    return await SellerController.login(payload, db)

@seller_router.post("/refresh")
async def refresh(payload: RefreshRequest, current_user: Seller = Depends(get_current_user_dep(Seller))):
    tokens = await cache_refresh_tokens(current_user.id, payload.refresh_token)
    return tokens

@seller_router.get("/me", response_model=SellerOut)
async def me(current_user: Seller = Depends(get_current_user_dep(Seller))):
    return current_user

@seller_router.post("/change-password")
async def change_password(payload: ChangePasswordRequest, current_user=Depends(get_current_user_dep(Seller)), db: AsyncSession = Depends(get_db)):
    return await BuyerController.change_password(payload, current_user, db)