from langchain_text_splitters import RecursiveCharacterTextSplitter
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.core.logging import logger
from app.models.embed import Document
from app.services.embedding_model import encode_text


class RAGPipeline:
    splitter = RecursiveCharacterTextSplitter(chunk_size=settings.CHUNK_SIZE, chunk_overlap=settings.CHUNK_OVERLAP)

    @staticmethod
    async def ingest_document(content: str, db: AsyncSession):
        logger.info("Starting document ingestion")
        logger.debug(f"Document content length: {len(content)} characters")

        if not content.strip():
            logger.warning("Document content is empty")
            return

        logger.debug(f"Splitting document with chunk_size={settings.CHUNK_SIZE}, chunk_overlap={settings.CHUNK_OVERLAP}")
        chunks = RAGPipeline.splitter.split_text(content)
        logger.info(f"Created {len(chunks)} chunks")

        if not chunks:
            logger.warning("No chunks generated from document")
            return

        logger.debug(f"First chunk preview: {chunks[0][:100]!r}")
        logger.info(f"Generating embeddings for {len(chunks)} chunks")

        try:
            embeddings = await encode_text(chunks)
            logger.info(f"Successfully generated {len(embeddings)} embeddings")
            logger.debug(f"Embedding dimension: {len(embeddings[0])}")
        except Exception:
            logger.exception("Failed to generate embeddings")
            raise

        logger.debug("Creating Document database records")
        documents = [Document(content=chunk, embedding=list(embedding)) for chunk, embedding in zip(chunks, embeddings)]
        logger.debug(f"Created {len(documents)} Document objects")

        logger.info(f"Saving {len(documents)} document chunks to database")

        try:
            db.add_all(documents)
            await db.commit()
            logger.info(f"Successfully ingested {len(documents)} document chunks")
        except Exception:
            logger.exception("Failed to save document chunks to database")
            await db.rollback()
            raise

    @staticmethod
    async def retrieve_documents(query: str, db: AsyncSession, limit: int = 5) -> list[Document]:
        logger.info("Starting document retrieval")
        logger.debug(f"Retrieval query: {query!r}")
        logger.debug(f"Retrieval limit: {limit}")

        if not query.strip():
            logger.warning("Empty retrieval query")
            return []

        logger.debug("Generating embedding for retrieval query")

        try:
            embedding = await encode_text(query)
            logger.debug(f"Query embedding generated with dimension: {len(embedding[0])}")
            query_embedding = embedding[0].tolist()
        except Exception:
            logger.exception("Failed to generate embedding for retrieval query")
            raise

        logger.info(f"Searching vector database for top {limit} documents")

        try:
            result = await db.scalars(select(Document).order_by(Document.embedding.cosine_distance(query_embedding)).limit(limit))
            documents = result.all()
            logger.info(f"Retrieved {len(documents)} documents")

            if documents:
                logger.debug(f"First retrieved document preview: {documents[0].content[:100]!r}")
            else:
                logger.warning("Vector search returned no documents")

            return documents
        except Exception:
            logger.exception("Failed to retrieve documents from vector database")
            raise