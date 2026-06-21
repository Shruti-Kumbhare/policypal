import os

# ── Embedding ──────────────────────────────────────────────────────────────────
EMBEDDING_MODEL = "BAAI/bge-base-en-v1.5"

# ── ChromaDB — Chroma Cloud ────────────────────────────────────────────────────
CHROMA_TENANT   = os.environ.get("CHROMA_TENANT", "")
CHROMA_DATABASE = os.environ.get("CHROMA_DATABASE", "policypal")
CHROMA_API_KEY  = os.environ.get("CHROMA_API_KEY", "")
COLLECTION_NAME = "policypal"

# ── Chunking ───────────────────────────────────────────────────────────────────
CHUNK_SIZE    = 400
CHUNK_OVERLAP = 50

# ── Retrieval ──────────────────────────────────────────────────────────────────
TOP_K                = 5
RELEVANCE_THRESHOLD  = 0.4

# ── LLM ───────────────────────────────────────────────────────────────────────
GROQ_API_KEY  = os.environ.get("GROQ_API_KEY", "")
GROQ_MODEL    = "llama-3.1-8b-instant"
MAX_TOKENS    = 500
TEMPERATURE   = 0.1
