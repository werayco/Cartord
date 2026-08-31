import asyncio
from app.core.logging import logger
from app.core.config import settings
from google import genai

class EmbeddingService:
    def __init__(self):
        self._use_local = settings.USE_LOCAL_EMBEDDING_MODEL
        if self._use_local:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(settings.LOCAL_EMBEDDING_MODEL, device="cpu")
        else:
            self._client = genai.Client(api_key=settings.GEMINI_API_KEY)

    async def encode(self, text: str | list[str]) -> list[list[float]]:
        inputs = [text] if isinstance(text, str) else text
        try:
            if self._use_local:
                return await self._encode_local(inputs)
            return await self._encode_gemini(inputs)
        except Exception:
            logger.exception("embedding encode failed")
            raise

    async def _encode_local(self, inputs: list[str]) -> list[list[float]]:
        vectors = await asyncio.to_thread(self._model.encode, inputs, batch_size=32)
        return vectors.tolist()

    async def _encode_gemini(self, inputs: list[str]) -> list[list[float]]:
        response = await self._client.aio.models.embed_content(
            model=settings.GEMINI_EMBEDDING_MODEL,
            contents=inputs,
        )
        return [e.values for e in response.embeddings]

embedding_service = EmbeddingService()

async def encode_text(text: str | list[str]):
    return await embedding_service.encode(text)