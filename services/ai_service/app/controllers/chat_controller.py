import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.conversation import Conversation
from app.models.message import Message
from app.models.outbox import OutboxEvent
from app.core.logging import logger

class ChatController:
    @staticmethod
    async def handle_message(websocket, data: dict, db: AsyncSession, user_id: uuid.UUID):
        try:
            conversation_id = data.get("conversation_id")
            message_id = data.get("message_id")
            content = data["content"]

            if not message_id:
                message_id = str(uuid.uuid4())

            message_id = uuid.UUID(message_id)

            if conversation_id:
                conversation_id = uuid.UUID(conversation_id)

                result = await db.execute(
                    select(Conversation).where(Conversation.id == conversation_id)
                )
                conversation = result.scalar_one_or_none()

                if conversation is None:
                    await websocket.send_json({
                        "type": "error",
                        "error": "Conversation not found",
                    })
                    return

                if conversation.user_id != user_id:
                    logger.warning(
                        f"User {user_id} attempted to post to conversation {conversation_id} owned by {conversation.user_id}"
                    )
                    await websocket.send_json({
                        "type": "error",
                        "error": "Conversation not found",
                    })
                    return
            else:
                conversation = Conversation(user_id=user_id)
                db.add(conversation)
                await db.flush()
                conversation_id = conversation.id
                logger.info(f"Created new conversation {conversation_id} for user {user_id}")

            message = Message(id=message_id,conversation_id=conversation_id,role="user",content=content)
            db.add(message)
            event = OutboxEvent(
                event_type="message.created",
                conversation_id=conversation_id,
                payload={
                    "message_id": str(message_id),
                    "conversation_id": str(conversation_id),
                    "user_id": str(user_id),
                    "content": content,
                },
            )
            db.add(event)

            await db.commit()

            await websocket.send_json({
                "ack": "200",
                "message_id": str(message_id),
                "conversation_id": str(conversation_id),
            })

        except KeyError as e:
            logger.error(f"Missing required field: {e}")
            await websocket.send_json({
                "type": "error",
                "error": f"Missing required field: {e}"
            })
        except ValueError as e:
            logger.error(f"Invalid UUID format: {e}")
            await websocket.send_json({
                "type": "error",
                "error": "Invalid ID format"
            })
        except Exception as e:
            logger.error(f"Error handling message: {e}")
            await websocket.send_json({
                "type": "error",
                "error": "Internal server error"
            })
            await db.rollback()
            raise