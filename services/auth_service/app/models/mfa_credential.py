from uuid import UUID
from sqlalchemy import BigInteger, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column
from app.db.session import Base


class MFACredential(Base):
    __tablename__ = "mfa_credential"

    account_type: Mapped[str] = mapped_column(String(16), primary_key=True)
    user_id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    encrypted_secret: Mapped[str] = mapped_column(String, nullable=False)
    last_used_counter: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
