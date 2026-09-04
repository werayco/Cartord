from app.db.session import Base
from sqlalchemy import Integer, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column
import uuid
from datetime import datetime


class SellerWallet(Base):
    __tablename__ = 'seller_wallet'

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    seller_id: Mapped[uuid.UUID] = mapped_column(nullable=False, unique=True, index=True)
    initial_amount: Mapped[float] = mapped_column(Integer, nullable=False, default=0)
    current_balance: Mapped[float] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())