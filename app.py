import os
import gradio as gr
import PyPDF2
import docx
from sentence_transformers import SentenceTransformer
import chromadb
import torch
import hashlib
from groq import Groq

# ── Setup ──────────────────────────────────────────────────────────────────────
device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"🖥️ Using device: {device}")

print("Loading embedding model...")
# Upgraded bge-base-en-v1.5
# Better semantic understanding, especially for domain-specific policy language
embedder = SentenceTransformer("BAAI/bge-base-en-v1.5", device=device)
print("✅ Embedding model loaded")

# PersistentClient instead of in-memory Client
# Collection survives session restarts — no need to re-upload documents every time
chroma_client = chromadb.PersistentClient(path="./chroma_db")
print("✅ ChromaDB initialized (persistent)")

groq_client = Groq(api_key=os.environ["GROQ_API_KEY"])
print("✅ Groq client ready")

MODEL = "llama-3.1-8b-instant"


# ── Document Parsing ───────────────────────────────────────────────────────────
def extract_text(file_path: str) -> str:
    text = ""
    if file_path.endswith(".pdf"):
        with open(file_path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                text += page.extract_text() or ""
    elif file_path.endswith(".docx"):
        doc = docx.Document(file_path)
        for para in doc.paragraphs:
            text += para.text + "\n"
    elif file_path.endswith(".txt"):
        with open(file_path, "r", encoding="utf-8") as f:
            text = f.read()
    return text.strip()


def split_into_chunks(text: str, chunk_size: int = 400, overlap: int = 50) -> list:
    words = text.split()
    chunks = []
    for i in range(0, len(words), chunk_size - overlap):
        chunk = " ".join(words[i:i + chunk_size])
        if chunk:
            chunks.append(chunk)
    return chunks


# ── Ingestion Pipeline ─────────────────────────────────────────────────────────
def get_or_create_collection(name: str = "policypal"):
    try:
        return chroma_client.get_collection(name)
    except:
        return chroma_client.create_collection(name)
    
def ingest_document(file_path: str, collection_name: str = "policypal") -> dict:
    text = extract_text(file_path)
    if not text:
        return {"error": "Could not extract text from document"}

    chunks = split_into_chunks(text)
    
    # BGE models perform better with a query prefix during encoding
    prefixed_chunks = [f"passage: {c}" for c in chunks]
    embeddings = embedder.encode(prefixed_chunks, show_progress_bar=False)

    collection = get_or_create_collection(collection_name)
    
    file_hash = hashlib.md5(file_path.encode()).hexdigest()[:8]
    ids = [f"{file_hash}_chunk_{i}" for i in range(len(chunks))]
    
    # Skip already-ingested chunks (duplicate guard)
    existing = collection.get(ids=ids)["ids"]
    new_indices = [i for i, id_ in enumerate(ids) if id_ not in existing]
    
    if not new_indices:
        return {"file": file_path, "characters": len(text), "chunks": 0, "skipped": True}
    
    collection.add(
        documents=[chunks[i] for i in new_indices],
        embeddings=[embeddings[i].tolist() for i in new_indices],
        ids=[ids[i] for i in new_indices],
        metadatas=[{"source": file_path, "chunk_index": i} for i in new_indices]
    )

    return {
        "file": file_path,
        "characters": len(text),
        "chunks": len(new_indices),
        "collection": collection_name
    }

# ── RAG Query Pipeline ─────────────────────────────────────────────────────────
def retrieve(query: str, collection_name: str = "policypal", top_k: int = 5) -> list:
    #  top_k 5, plus relevance threshold filter
    try:
        collection = chroma_client.get_collection(collection_name)
    except:
        return []

    # BGE query prefix for retrieval
    prefixed_query = f"query: {query}"
    query_embedding = embedder.encode([prefixed_query]).tolist()
    results = collection.query(query_embeddings=query_embedding, n_results=top_k)

    chunks = results["documents"][0]
    metadatas = results["metadatas"][0]
    distances = results["distances"][0]

    retrieved = []
    for chunk, meta, dist in zip(chunks, metadatas, distances):
        score = round(max(0, 1 - dist / 2), 3)
        # ✅ Filter out low-relevance chunks (score < 0.4 = noise)
        if score >= 0.4:
            retrieved.append({
                "chunk": chunk,
                "source": meta["source"],
                "chunk_index": meta["chunk_index"],
                "relevance_score": score
            })

    return retrieved


def generate_answer(query: str, retrieved_chunks: list) -> str:
    context = "\n\n---\n\n".join([r["chunk"] for r in retrieved_chunks])
    prompt = f"""You are PolicyPal, an HR policy assistant.
Answer the question using ONLY the context provided below.
If the answer is not in the context, say: "I couldn't find that in the uploaded documents."
Always be specific and cite which part of the policy answers the question.

Context:
{context}

Question: {query}

Answer:"""

    response = groq_client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,
        max_tokens=500
    )
    return response.choices[0].message.content


# ── Gradio UI ──────────────────────────────────────────────────────────────────
# Multi-file upload — loops over all files, reports per-file status
def upload_and_ingest(files):
    if not files:
        return "❌ Please upload at least one file"

    results = []
    for file in files:
        result = ingest_document(file.name)
        if "error" in result:
            results.append(f"❌ {file.name.split('/')[-1]}: {result['error']}")
        elif result.get("skipped"):
            results.append(f"⚠️ {result['file'].split('/')[-1]} — already ingested, skipped")
        else:
            results.append(
                f"✅ {result['file'].split('/')[-1]}\n"
                f"   📦 Chunks: {result['chunks']} | 🔤 Characters: {result['characters']}"
            )

    return "\n\n".join(results)


def ask_question(question):
    if not question.strip():
        return "Please enter a question.", ""
    try:
        retrieved = retrieve(question)
        if not retrieved:
            return "⚠️ No relevant content found. Try rephrasing, or upload a document first.", ""
        answer = generate_answer(question, retrieved)
        sources_text = "\n\n".join([
            f"📎 Source {i+1} (relevance: {r['relevance_score']}) — {r['source'].split('/')[-1]}:\n{r['chunk'][:150]}..."
            for i, r in enumerate(retrieved)
        ])
        return answer, sources_text
    except Exception as e:
        return f"❌ Error: {str(e)}", ""


with gr.Blocks(title="PolicyPal", theme=gr.themes.Soft()) as demo:
    gr.Markdown("# 📋 PolicyPal — HR Policy Assistant")
    gr.Markdown("Upload your HR policy documents and ask questions in plain English.")

    with gr.Tab("📤 Upload Document"):
        file_input = gr.File(
            label="Upload PDF, DOCX, or TXT files",
            file_count="multiple"       # multi-file
        )
        upload_btn = gr.Button("Ingest Documents", variant="primary")
        upload_output = gr.Textbox(label="Status", lines=6)
        upload_btn.click(upload_and_ingest, inputs=file_input, outputs=upload_output)

    with gr.Tab("💬 Ask Questions"):
        question_input = gr.Textbox(
            label="Your Question",
            placeholder="e.g. How many sick leaves do I get per year?",
            lines=2
        )
        ask_btn = gr.Button("Ask PolicyPal", variant="primary")
        answer_output = gr.Textbox(label="Answer", lines=5)
        sources_output = gr.Textbox(label="Sources Used", lines=6)
        ask_btn.click(
            ask_question,
            inputs=question_input,
            outputs=[answer_output, sources_output]
        )

demo.launch(share=True)