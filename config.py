import os

# ── Embedding ──────────────────────────────────────────────────────────────────
EMBEDDING_MODEL = "BAAI/bge-base-en-v1.5"

# ── ChromaDB ───────────────────────────────────────────────────────────────────
CHROMA_PATH = "./chroma_db"
COLLECTION_NAME = "policypal"

# ── Chunking ───────────────────────────────────────────────────────────────────
CHUNK_SIZE = 400        # words per chunk (fallback for non-section docs)
CHUNK_OVERLAP = 50

# ── Retrieval ──────────────────────────────────────────────────────────────────
TOP_K = 5
RELEVANCE_THRESHOLD = 0.4

# ── LLM ───────────────────────────────────────────────────────────────────────
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
GROQ_MODEL = "llama-3.1-8b-instant"
MAX_TOKENS = 500
TEMPERATURE = 0.1
