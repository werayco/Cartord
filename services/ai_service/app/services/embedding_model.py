import asyncio
from sentence_transformers import SentenceTransformer
from app.core.logging import logger
from app.core.config import settings

model = SentenceTransformer(settings.EMBEDDING_MODEL, device="cpu")

async def encode_text(text: str | list[str]):
    inputs = [text] if isinstance(text, str) else text
    try:
        vectors = await asyncio.to_thread(model.encode, inputs, batch_size=32)
        return vectors
    except Exception:
        logger.exception("embedding encode failed")
        raise