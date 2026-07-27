from uuid import UUID
from sqlalchemy import String, Uuid
from sqlalchemy.orm import Mapped, mapped_column
from uuid6 import uuid7
from app.db.session import Base

class Order(Base):
    __tablename__ = "order_table"