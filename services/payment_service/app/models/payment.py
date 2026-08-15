from datetime import datetime
from uuid import UUID
from sqlalchemy import String, Uuid, Numeric, DateTime, Enum, func
from sqlalchemy.orm import Mapped, mapped_column
from uuid6 import uuid7
from app.db.session import Base
from app.core.schemas import PaymentStatus

class Payment(Base):
    __tablename__ = "payment"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid7)
    customer_id: Mapped[UUID] = mapped_column(Uuid, nullable=False, index=True)
    order_id: Mapped[UUID] = mapped_column(Uuid, nullable=False, unique=True, index=True)
    sku: Mapped[str] = mapped_column(String(50), nullable=False)
    subtotal: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    status: Mapped[PaymentStatus] = mapped_column(Enum(PaymentStatus), nullable=False, default=PaymentStatus.PENDING)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())