import os
import hashlib
import chromadb
from config import (
    CHROMA_TENANT, CHROMA_DATABASE, CHROMA_API_KEY, COLLECTION_NAME
)
from ingestion.parser import extract_text
from ingestion.chunker import chunk_text
from ingestion.embedder import encode_passages

BATCH = 100

# ── Chroma Cloud client ───────────────────────────────────────────────────────
_client = chromadb.CloudClient(
    tenant=CHROMA_TENANT,
    database=CHROMA_DATABASE,
    api_key=CHROMA_API_KEY,
)


def get_or_create_collection(name: str = COLLECTION_NAME):
    try:
        return _client.get_collection(name)
    except Exception:
        return _client.create_collection(name)


def get_collection(name: str = COLLECTION_NAME):
    return _client.get_collection(name)


def list_documents(collection_name: str = COLLECTION_NAME) -> list[str]:
    """Return unique source file names currently in the collection."""
    try:
        col = get_collection(collection_name)
        results = col.get(include=["metadatas"])
        names = {m["source_name"] for m in results["metadatas"] if "source_name" in m}
        return sorted(names)
    except Exception:
        return []


def _file_hash(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def ingest_document(file_path: str, collection_name: str = COLLECTION_NAME,
                    original_filename: str = None) -> dict:
    display_name = original_filename or os.path.basename(file_path)
    doc_hash = _file_hash(file_path)
    collection = get_or_create_collection(collection_name)

    # 1. Identical content already stored (under any filename) -> skip
    if collection.get(where={"doc_hash": doc_hash}, limit=1)["ids"]:
        return {"file": display_name, "characters": None,
                "chunks_added": 0, "chunks_skipped": 0, "already_ingested": True}

    text = extract_text(file_path)
    if not text:
        return {"file": display_name, "error": "Could not extract text from document"}

    # 2. Same filename, different content -> replace old chunks after new ones land
    old_ids = set(collection.get(where={"source_name": display_name})["ids"])

    chunks = chunk_text(text)
    texts = [c["text"] for c in chunks]
    ids = [f"{doc_hash[:16]}_{i}" for i in range(len(chunks))]
    metadatas = [
        {
            "source": display_name,
            "source_name": display_name,
            "doc_hash": doc_hash,
            "section": c["section"],
            "section_index": c["section_index"],
            "chunk_index": i,
        }
        for i, c in enumerate(chunks)
    ]

    for s in range(0, len(ids), BATCH):
        sl = slice(s, s + BATCH)
        collection.upsert(
            ids=ids[sl],
            documents=texts[sl],
            embeddings=encode_passages(texts[sl]),
            metadatas=metadatas[sl],
        )

    stale = list(old_ids - set(ids))
    for s in range(0, len(stale), BATCH):
        collection.delete(ids=stale[s:s + BATCH])

    return {
        "file": display_name,
        "characters": len(text),
        "chunks_added": len(ids),
        "chunks_skipped": 0,
        "replaced_chunks": len(stale),
        "sections_detected": list({c["section"] for c in chunks if c["section"] != "unknown"})[:5],
    }