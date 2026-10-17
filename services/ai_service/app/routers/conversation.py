import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.schemas import ConversationRename
from app.core.utils import get_user
from app.db.session import get_db
from app.models.conversation import Conversation

router = APIRouter(prefix="/api/v1/conversations", tags=["conversations"])


@router.patch("/{conversation_id}")
async def rename_conversation(
    conversation_id: uuid.UUID,
    body: ConversationRename,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_user),
):
    result = await db.execute(
        update(Conversation)
        .where(
            Conversation.id == conversation_id,
            Conversation.user_id == uuid.UUID(current_user["id"]),
        )
        .values(title=body.title)
        .returning(Conversation.id, Conversation.title)
    )
    row = result.one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    await db.commit()

    return {"id": str(row.id), "title": row.title}