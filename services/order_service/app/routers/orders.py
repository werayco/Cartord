from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.utils import get_current_user_dep

order_router = APIRouter(prefix="/api/v1/order",tags=["order"])