from config import TOP_K, RELEVANCE_THRESHOLD, COLLECTION_NAME
from ingestion.embedder import encode_query
from retrieval.store import get_collection


def retrieve(query: str, collection_name: str = COLLECTION_NAME, top_k: int = TOP_K) -> list[dict]:
    """
    Embed query → vector search → filter by relevance threshold.
    Returns list of dicts with chunk text, source, section, and score.
    """
    try:
        collection = get_collection(collection_name)
    except Exception:
        return []

    query_embedding = encode_query(query)
    results = collection.query(query_embeddings=[query_embedding], n_results=top_k)

    chunks = results["documents"][0]
    metadatas = results["metadatas"][0]
    distances = results["distances"][0]

    retrieved = []
    for chunk, meta, dist in zip(chunks, metadatas, distances):
        score = round(max(0, 1 - dist / 2), 3)
        if score >= RELEVANCE_THRESHOLD:
            retrieved.append({
                "chunk": chunk,
                "source_name": meta.get("source_name", meta.get("source", "unknown")),
                "section": meta.get("section", "unknown"),
                "relevance_score": score,
            })

    return retrieved
