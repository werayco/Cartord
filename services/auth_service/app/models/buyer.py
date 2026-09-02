from datetime import datetime
from uuid import UUID
from sqlalchemy import String, Uuid, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column
from uuid6 import uuid7
from app.db.session import Base

class Buyer(Base):
    __tablename__ = "buyer"
    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid7)
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    username: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)
    password: Mapped[str] = mapped_column(String, nullable=False)
    shipping_address: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)