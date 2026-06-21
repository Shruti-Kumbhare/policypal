from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from retrieval.retriever import retrieve
from generation.generator import generate_answer

router = APIRouter()


class QueryRequest(BaseModel):
    question: str


class SourceItem(BaseModel):
    source_name:     str
    section:         str
    relevance_score: float
    excerpt:         str


class QueryResponse(BaseModel):
    answer:  str
    sources: list[SourceItem]


@router.post("/", response_model=QueryResponse)
async def ask(req: QueryRequest):
    if not req.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")

    retrieved = retrieve(req.question)

    if not retrieved:
        return QueryResponse(
            answer="I couldn't find relevant content. Try rephrasing or upload more documents.",
            sources=[]
        )

    answer = generate_answer(req.question, retrieved)

    sources = [
        SourceItem(
            source_name=r["source_name"],
            section=r["section"],
            relevance_score=r["relevance_score"],
            excerpt=r["chunk"][:200],
        )
        for r in retrieved
    ]

    return QueryResponse(answer=answer, sources=sources)
