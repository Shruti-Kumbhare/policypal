from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes import ingest, query, documents

app = FastAPI(
    title="PolicyPal API",
    description="HR Policy RAG backend",
    version="3.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # tighten in production
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ingest.router,    prefix="/ingest",    tags=["Ingestion"])
app.include_router(query.router,     prefix="/query",     tags=["Query"])
app.include_router(documents.router, prefix="/documents", tags=["Documents"])


@app.get("/health")
def health():
    return {"status": "ok", "service": "PolicyPal API v3"}
