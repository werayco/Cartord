from typing import Optional
from uuid import UUID
from sqlalchemy import String, Uuid, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from uuid6 import uuid7
from app.db.session import Base

class Employee(Base):
    __tablename__ = "employee"
    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid7)
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    username: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    is_admin: Mapped[str] = mapped_column(Boolean, nullable=False)
    password: Mapped[str] = mapped_column(String, nullable=False)