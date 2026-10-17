from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, Enum, Integer, Numeric, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column
from uuid6 import uuid7

from app.core.schemas import OrderStatus
from app.db.session import Base


class Order(Base):
    __tablename__ = "order"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid7)
    sku: Mapped[str] = mapped_column(String, nullable=False)
    customer_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)

    seller_id: Mapped[UUID | None] = mapped_column(Uuid, nullable=True, index=True)

    unit_price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    status: Mapped[OrderStatus] = mapped_column(
        Enum(OrderStatus), nullable=False, default=OrderStatus.PENDING
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
