from fastapi import APIRouter
from retrieval.store import list_documents

router = APIRouter()


@router.get("/")
def get_documents():
    """List all document names currently ingested in the collection."""
    docs = list_documents()
    return {"documents": docs, "count": len(docs)}
