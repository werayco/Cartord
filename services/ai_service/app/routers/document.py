from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.services.doc_parser import extract_text
from app.services.rag_pipeline import RAGPipeline


router = APIRouter(prefix="/api/v1/documents",tags=["documents"])


@router.post("/upload")
async def upload_document(file: UploadFile = File(...),db: AsyncSession = Depends(get_db)):
    text = await extract_text(file)
    await RAGPipeline.ingest_document(content=text,db=db)

    return {
        "message": "Document successfully ingested",
        "filename": file.filename,
    }