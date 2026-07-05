"""
api/routes/document.py
──────────────────────
Lists all documents currently ingested in the vector store.
"""

from fastapi import APIRouter
from retrieval.store import list_documents
from api.schemas.document import DocumentListResponse

router = APIRouter()


@router.get("/", response_model=DocumentListResponse)
async def get_documents():
    """Return all unique document names currently in the vector store."""
    docs = list_documents()
    return DocumentListResponse(documents=docs, count=len(docs))
