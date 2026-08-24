import enum
import uuid
from datetime import datetime
from app.db.session import Base
from sqlalchemy import Enum, ForeignKey, Text, Uuid, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from uuid6 import uuid7

class MessageRole(str, enum.Enum):
    user = "user"
    assistant = "assistant"
    system = "system"

class Message(Base):
    __tablename__ = "messages"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid7)
    conversation_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True),ForeignKey("conversations.id", ondelete="CASCADE"),nullable=False,index=True)
    role: Mapped[MessageRole] = mapped_column(Enum(MessageRole, name="message_role"), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)