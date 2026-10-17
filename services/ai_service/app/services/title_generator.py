import json
import uuid
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_groq import ChatGroq
from sqlalchemy import update
from app.core.config import settings
from app.core.logging import logger
from app.db.redis_client import redis_client
from app.db.session import AsyncSessionLocal
from app.models.conversation import Conversation
from app.services.socket_registry import conversation_channel

title_llm = ChatGroq(
    model="openai/gpt-oss-safeguard-20b", # openai/gpt-oss-safeguard-20b
    api_key=settings.LLM_API_KEY,
    temperature=0.2,
)

TITLE_PROMPT = (
    "Write a short title (max 6 words) for a chat that begins with the user message below. "
    "Use the same language as the message. No quotes, no trailing punctuation. "
    "Reply with the title only."
)

def _clean(raw: str, fallback: str) -> str:
    title = (raw or "").strip().splitlines()[0].strip(" \"'.") if raw and raw.strip() else ""
    title = title or fallback.strip()
    return title[:60]

async def generate_and_publish_title(conversation_id: str, first_message: str) -> None:
    try:
        result = await title_llm.ainvoke(
            [SystemMessage(content=TITLE_PROMPT), HumanMessage(content=first_message[:1000])]
        )
        title = _clean(result.content, fallback=first_message)

        async with AsyncSessionLocal() as db:
            res = await db.execute(
                update(Conversation)
                .where(Conversation.id == uuid.UUID(conversation_id), Conversation.title.is_(None))
                .values(title=title)
            )
            await db.commit()
            if res.rowcount == 0:
                return

        await redis_client.publish(conversation_channel(conversation_id), json.dumps({
            "type": "title",
            "conversation_id": conversation_id,
            "title": title,
        }))
    except Exception as e:
        logger.error(f"Title generation failed for {conversation_id}: {e}")  # never fail the chat turn