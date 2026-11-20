from datetime import datetime
from uuid import UUID

from sqlalchemy import Boolean, DateTime, Integer, Numeric, Sequence, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base

sku_seq = Sequence("inventory_sku_seq", start=1, minvalue=1, metadata=Base.metadata)


class Inventory(Base):
    __tablename__ = "inventory"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)
    unit_price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)

    sku: Mapped[str] = mapped_column(
        String(50), primary_key=True, autoincrement=False, unique=True
    )
    available_quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    reserved_quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    seller_id: Mapped[UUID | None] = mapped_column(Uuid, nullable=True, index=True)

    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )
    images: Mapped[list["ProductImage"]] = relationship(
        "ProductImage",
        back_populates="product",
        cascade="all, delete-orphan",
        order_by="ProductImage.sort_order",
        passive_deletes=True,
    )
