"""
api/main.py
───────────
FastAPI application factory for PolicyPal.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes import ingest, query, document
from api.schemas.health import HealthResponse

app = FastAPI(
    title="PolicyPal API",
    description="HR Policy RAG backend — upload documents, ask questions.",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # tighten in production
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ingest.router,   prefix="/ingest",    tags=["Ingestion"])
app.include_router(query.router,    prefix="/query",     tags=["Query"])
app.include_router(document.router, prefix="/documents", tags=["Documents"])


@app.get("/health", response_model=HealthResponse)
def health():
    return HealthResponse(
        status="ok",
        service="PolicyPal API",
        version="2.0.0"
    )
