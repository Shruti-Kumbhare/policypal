"""
api/schemas/query.py
─────────────────────
Pydantic models for question answering endpoints.
"""

from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    """Request body for asking a question."""
    question: str = Field(
        ...,
        min_length=3,
        max_length=500,
        description="The question to ask about the uploaded policy documents."
    )


class SourceItem(BaseModel):
    """A single retrieved source chunk used to generate the answer."""
    source_name:     str
    section:         str
    relevance_score: float
    excerpt:         str


class QueryResponse(BaseModel):
    """Response returned after a question is answered."""
    question:   str
    answer:     str
    sources:    list[SourceItem]
    latency_ms: float
