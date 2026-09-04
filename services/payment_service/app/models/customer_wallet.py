from app.db.session import Base
from sqlalchemy import Integer, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column
import uuid
from datetime import datetime

class UserWallet(Base):
    __tablename__ = 'user_wallet'
    
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    customer_id: Mapped[uuid.UUID] = mapped_column(nullable=False, unique=True, index=True)
    initial_amount: Mapped[float] = mapped_column(Integer, nullable=False, default=100000)
    current_balance: Mapped[float] = mapped_column(Integer, nullable=False, default=100000)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())