import hashlib
import chromadb
from config import CHROMA_PATH, COLLECTION_NAME
from ingestion.parser import extract_text
from ingestion.chunker import chunk_text
from ingestion.embedder import encode_passages


_client = chromadb.PersistentClient(path=CHROMA_PATH)
print("✅ ChromaDB initialized (persistent)")


def get_or_create_collection(name: str = COLLECTION_NAME):
    try:
        return _client.get_collection(name)
    except Exception:
        return _client.create_collection(name)


def get_collection(name: str = COLLECTION_NAME):
    return _client.get_collection(name)


def ingest_document(file_path: str, collection_name: str = COLLECTION_NAME) -> dict:
    """
    Parse → section-chunk → embed → store in ChromaDB.
    Returns a summary dict with chunk count, skipped count, and section info.
    """
    text = extract_text(file_path)
    if not text:
        return {"error": "Could not extract text from document"}

    chunks = chunk_text(text)
    file_hash = hashlib.md5(file_path.encode()).hexdigest()[:8]

    ids = [f"{file_hash}_sec{c['section_index']}_chunk{i}" for i, c in enumerate(chunks)]
    texts = [c["text"] for c in chunks]
    metadatas = [
        {
            "source": file_path,
            "source_name": file_path.split("/")[-1],
            "section": c["section"],
            "section_index": c["section_index"],
        }
        for c in chunks
    ]

    collection = get_or_create_collection(collection_name)

    # Duplicate guard
    existing_ids = set(collection.get(ids=ids)["ids"])
    new_indices = [i for i, id_ in enumerate(ids) if id_ not in existing_ids]

    if not new_indices:
        return {
            "file": file_path,
            "characters": len(text),
            "chunks_added": 0,
            "chunks_skipped": len(ids),
            "already_ingested": True,
        }

    embeddings = encode_passages([texts[i] for i in new_indices])

    collection.add(
        documents=[texts[i] for i in new_indices],
        embeddings=embeddings,
        ids=[ids[i] for i in new_indices],
        metadatas=[metadatas[i] for i in new_indices],
    )

    sections_found = list({c["section"] for c in chunks if c["section"] != "unknown"})

    return {
        "file": file_path,
        "characters": len(text),
        "chunks_added": len(new_indices),
        "chunks_skipped": len(ids) - len(new_indices),
        "sections_detected": sections_found[:5],   # preview first 5
    }
