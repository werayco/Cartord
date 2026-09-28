from langchain_text_splitters import RecursiveCharacterTextSplitter
from sqlalchemy import select, func
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
    async def retrieve_documents(query: str,db: AsyncSession,limit: int = 5,candidate_limit: int = 20,rrf_k: int = 60) -> list[Document]:
        logger.info("Starting hybrid document retrieval")
        logger.debug(f"Retrieval query: {query!r}")
        logger.debug(f"limit={limit}, candidate_limit={candidate_limit}, rrf_k={rrf_k}")

        if not query.strip():
            logger.warning("Empty retrieval query")
            return []

        logger.debug("Generating embedding for retrieval query")
        try:
            embedding = await encode_text(query)
            print(dir(embedding))
            query_embedding = embedding[0]
        except Exception:
            logger.exception("Failed to generate embedding for retrieval query")
            raise

        ts_query = func.websearch_to_tsquery("english", query)
        vector_rank = (
            select(
                Document.id,
                func.row_number()
                .over(order_by=Document.embedding.cosine_distance(query_embedding))
                .label("rank"),
            )
            .order_by(Document.embedding.cosine_distance(query_embedding))
            .limit(candidate_limit)
            .cte("vector_rank")
        )

        fts_rank = (select(Document.id,func.row_number().over(order_by=func.ts_rank(Document.content_tsv, ts_query).desc()).label("rank"))
            .where(Document.content_tsv.op("@@")(ts_query))
            .order_by(func.ts_rank(Document.content_tsv, ts_query).desc())
            .limit(candidate_limit)
            .cte("fts_rank")
        )

        rrf_score = (
            func.coalesce(1.0 / (rrf_k + vector_rank.c.rank), 0.0)
            + func.coalesce(1.0 / (rrf_k + fts_rank.c.rank), 0.0)
        ).label("rrf_score")

        fused = (
            select(
                func.coalesce(vector_rank.c.id, fts_rank.c.id).label("id"),
                rrf_score,
            )
            .select_from(
                vector_rank.outerjoin(
                    fts_rank, vector_rank.c.id == fts_rank.c.id, full=True
                )
            )
            .cte("fused")
        )

        final_stmt = (
            select(Document)
            .join(fused, Document.id == fused.c.id)
            .order_by(fused.c.rrf_score.desc())
            .limit(limit)
        )

        logger.info(
            f"Running hybrid search (vector + FTS, RRF k={rrf_k}, "
            f"candidate_limit={candidate_limit}) for top {limit} documents"
        )

        try:
            result = await db.scalars(final_stmt)
            documents = result.all()
            logger.info(f"Retrieved {len(documents)} documents")

            if documents:
                logger.debug(f"First retrieved document preview: {documents[0].content[:100]!r}")
            else:
                logger.warning("Hybrid search returned no documents")

            return documents
        except Exception:
            logger.exception("Failed to retrieve documents from vector database")
            raise