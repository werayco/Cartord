from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import Conversation, Message, OutboxEvent
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.schemas import Conversation
from app.models import Conversation, Message, OutboxEvent

class WebsocketController:
    @staticmethod
    async def db_input(message: Conversation,role: MessageRole,user_id: UUID,content: str, db: AsyncSession,) -> Message:
        conversation = await db.get(Conversation, message.id)

        if conversation is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Conversation not found")

        if conversation.user_id != user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="You do not have access to this conversation")

        new_message = Message(conversation_id=conversation.id,role=role,content=content)

        db.add(new_message)

        await db.flush()

        outbox_event = OutboxEvent(event_type="message.created",conversation_id=conversation.id,payload={"message_id": str(new_message.id),"conversation_id": str(conversation.id),"user_id": str(user_id),"role": role.value,"content": content})
        db.add(outbox_event)

        await db.commit()
        await db.refresh(new_message)
        await db.refresh(outbox_event)

        return new_message