"""
api/schemas/document.py
────────────────────────
Pydantic models for document listing endpoints.
"""

from pydantic import BaseModel


class DocumentListResponse(BaseModel):
    """Response listing all ingested documents in the vector store."""
    documents: list[str]
    count:     int
