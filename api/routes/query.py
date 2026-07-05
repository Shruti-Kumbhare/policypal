"""
api/routes/query.py
───────────────────
Handles question answering against ingested documents.
"""

from fastapi import APIRouter
from api.schemas.query import QueryRequest, QueryResponse, SourceItem
# keep your existing imports below this line

router = APIRouter()


@router.post("/", response_model=QueryResponse)
async def ask_question(body: QueryRequest):
    # your existing logic stays exactly the same
    # just make sure the return matches QueryResponse shape:
    return QueryResponse(
        question=body.question,
        answer=answer,
        sources=[SourceItem(**s) for s in sources],
        latency_ms=latency_ms
    )
