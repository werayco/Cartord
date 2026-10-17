from uuid import UUID

from pgvector.sqlalchemy import VECTOR
from sqlalchemy import Computed, Index, Text, Uuid
from sqlalchemy.dialects.postgresql import TSVECTOR
from sqlalchemy.orm import Mapped, mapped_column
from uuid6 import uuid7

from app.db.session import Base


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid7)
    content: Mapped[str] = mapped_column(Text)
    embedding: Mapped[list[float]] = mapped_column(VECTOR(3072))
    content_tsv: Mapped[str] = mapped_column(
        TSVECTOR,
        Computed("to_tsvector('english', content)", persisted=True),
    )

    __table_args__ = (
        Index("documents_content_tsv_idx", "content_tsv", postgresql_using="gin"),
    )
