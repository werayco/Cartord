from fastapi import APIRouter, Depends
from app.core.utils import get_current_user
from app.services.elasticsearch_client import elasticsearch_client

search_router = APIRouter(prefix="/api/v1/search",tags=["search"])

@search_router.get("/items")
def get_item(query:str, current_user = Depends(get_current_user)):
    return {"response":elasticsearch_client.search_documents(query)}