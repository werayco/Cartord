from typing import Optional
from uuid import UUID
from sqlalchemy import String, Uuid, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from uuid6 import uuid7
from app.db.session import Base
from app.core.schemas import Roles
from sqlalchemy import Enum

class Seller(Base):
    __tablename__ = "seller"
    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid7)
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    username: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    role: Mapped[str] = mapped_column(Enum(Roles, native_enum=False, values_callable=lambda enum_cls: [e.value for e in enum_cls]), nullable=False)
    password: Mapped[str] = mapped_column(String, nullable=False)