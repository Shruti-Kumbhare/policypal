import torch
from sentence_transformers import SentenceTransformer
from config import EMBEDDING_MODEL


device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"🖥️  Using device: {device}")

print(f"Loading embedding model: {EMBEDDING_MODEL} ...")
_embedder = SentenceTransformer(EMBEDDING_MODEL, device=device)
print("✅ Embedding model loaded")


def encode_passages(texts: list[str]) -> list[list[float]]:
    """Encode document chunks with BGE passage prefix."""
    prefixed = [f"passage: {t}" for t in texts]
    return _embedder.encode(prefixed, show_progress_bar=False).tolist()


def encode_query(query: str) -> list[float]:
    """Encode a user query with BGE query prefix."""
    return _embedder.encode([f"query: {query}"], show_progress_bar=False)[0].tolist()
