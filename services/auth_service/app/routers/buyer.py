from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.controllers.buyer_controller import BuyerController
from app.core.schemas import (
    BuyerOut,
    ChangePasswordRequest,
    DeleteUser,
    LoginRequest,
    MFAEnrollmentRequest,
    MFACodeRequest,
    MFALoginRequest,
    RefreshRequest,
    RegisterRequest,
    UpdateUser,
)
from app.core.utils import cache_refresh_tokens, get_current_user_dep
from app.db.session import get_db
from app.models.buyer import Buyer
from app.services.mfa import confirm_enrollment, start_enrollment

buyer_router = APIRouter(prefix="/api/v1/auth/buyer", tags=["auth"])


@buyer_router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(payload: RegisterRequest, db: AsyncSession = Depends(get_db)):
    return await BuyerController.register(payload, db)


@buyer_router.post("/login")
async def login(payload: LoginRequest, db: AsyncSession = Depends(get_db)):
    return await BuyerController.login(payload, db)


@buyer_router.post("/login/mfa")
async def complete_mfa_login(
    payload: MFALoginRequest, db: AsyncSession = Depends(get_db)
):
    return await BuyerController.complete_mfa_login(payload, db)


@buyer_router.post("/mfa/enrollment")
async def begin_mfa_enrollment(
    payload: MFAEnrollmentRequest,
    current_user: Buyer = Depends(get_current_user_dep(Buyer)),
    db: AsyncSession = Depends(get_db),
):
    return await start_enrollment(current_user, "buyer", payload.password, db)


@buyer_router.post("/mfa/enrollment/verify")
async def verify_mfa_enrollment(
    payload: MFACodeRequest,
    current_user: Buyer = Depends(get_current_user_dep(Buyer)),
    db: AsyncSession = Depends(get_db),
):
    return await confirm_enrollment(current_user, "buyer", payload.code, db)


@buyer_router.post("/refresh")
async def refresh(
    payload: RefreshRequest, current_user: Buyer = Depends(get_current_user_dep(Buyer))
):
    tokens = await cache_refresh_tokens(
        current_user.id, payload.refresh_token, current_user
    )
    return tokens


@buyer_router.get("/me", response_model=BuyerOut)
async def me(current_user: Buyer = Depends(get_current_user_dep(Buyer))):
    return current_user


@buyer_router.post("/change-password")
async def change_password(
    payload: ChangePasswordRequest,
    current_user: Buyer = Depends(get_current_user_dep(Buyer)),
    db: AsyncSession = Depends(get_db),
):
    return await BuyerController.change_password(payload, current_user, db)


@buyer_router.patch("/update")
async def update_user(
    payload: UpdateUser,
    current_user: Buyer = Depends(get_current_user_dep(Buyer)),
    db: AsyncSession = Depends(get_db),
):
    return await BuyerController.update_user(payload, db, current_user)


@buyer_router.delete("/delete")
async def delete_user(
    payload: DeleteUser,
    current_user: Buyer = Depends(get_current_user_dep(Buyer)),
    db: AsyncSession = Depends(get_db),
):
    return await BuyerController.delete_user(payload, db, current_user)
