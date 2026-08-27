from uuid import UUID
from pgvector.sqlalchemy import VECTOR
from sqlalchemy import Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column
from app.db.session import Base
from uuid6 import uuid7

class Document(Base):
    __tablename__ = "documents"

    id: Mapped[UUID] = mapped_column(Uuid,primary_key=True,default=uuid7)
    content: Mapped[str] = mapped_column(Text)
    embedding: Mapped[list[float]] = mapped_column(VECTOR(3072))