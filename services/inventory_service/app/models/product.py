from datetime import datetime
from uuid import UUID

from sqlalchemy import Boolean, DateTime, Integer, Numeric, Sequence, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base

# The database owns the counter that produces the "xxxx" in CTD-xxxx.
# The application only adds the "CTD-" prefix (see inventory_controller.py).
sku_seq = Sequence("inventory_sku_seq", start=1, minvalue=1, metadata=Base.metadata)


class Inventory(Base):
    __tablename__ = "inventory"

    # (id, sku) together are the composite primary key.
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)
    unit_price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)

    # Still unique on its own: other services (order, search, ai) look products up by sku alone.
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
