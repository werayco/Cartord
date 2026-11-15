from sqlalchemy import delete, select

from app.db.session import AsyncSessionLocal
from app.models.embed import Document
from app.services.rag_internal_data import DATA
from app.services.rag_pipeline import RAGPipeline


async def ingest_internal_data() -> None:
    chunks = RAGPipeline.splitter.split_text(DATA)
    async with AsyncSessionLocal() as db:
        stored = (await db.scalars(select(Document.content))).all()
        if stored and set(stored) == set(chunks):
            return
        await db.execute(delete(Document))
        await db.commit()
        await RAGPipeline.ingest_document(DATA, db)
