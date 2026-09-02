from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.services.doc_parser import extract_text
from app.services.rag_pipeline import RAGPipeline
from app.core.utils import get_admin, get_current_user

router = APIRouter(prefix="/api/v1/documents", tags=["documents"])

@router.post("/upload")
async def upload_document(file: UploadFile = File(...),db: AsyncSession = Depends(get_db),admin: dict = Depends(get_admin),):
    text = await extract_text(file)
    await RAGPipeline.ingest_document(content=text, db=db)
    return {"message": "Document successfully ingested","filename": file.filename}

@router.get("/query/{question}")
async def query_document(question: str,db: AsyncSession = Depends(get_db),current_user: dict = Depends(get_current_user),):
    document = await RAGPipeline.retrieve_documents(question, db)
    return {"message": "Document retrieved successfully","document_text": document}