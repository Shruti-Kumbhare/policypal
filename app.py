import os
import gradio as gr
import PyPDF2
import docx
from sentence_transformers import SentenceTransformer
import chromadb
import torch
from groq import Groq

# ── Setup ──────────────────────────────────────────────────────────────────────
device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"🖥️ Using device: {device}")

print("Loading embedding model...")
embedder = SentenceTransformer("all-MiniLM-L6-v2", device=device)
print("✅ Embedding model loaded")

chroma_client = chromadb.Client()
print("✅ ChromaDB initialized")

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
        chroma_client.delete_collection(name)
    except:
        pass
    return chroma_client.create_collection(name)


def ingest_document(file_path: str, collection_name: str = "policypal") -> dict:
    text = extract_text(file_path)
    if not text:
        return {"error": "Could not extract text from document"}

    chunks = split_into_chunks(text)
    embeddings = embedder.encode(chunks, show_progress_bar=False)

    collection = get_or_create_collection(collection_name)
    collection.add(
        documents=chunks,
        embeddings=embeddings.tolist(),
        ids=[f"chunk_{i}" for i in range(len(chunks))],
        metadatas=[{"source": file_path, "chunk_index": i} for i in range(len(chunks))]
    )

    return {
        "file": file_path,
        "characters": len(text),
        "chunks": len(chunks),
        "collection": collection_name
    }


# ── RAG Query Pipeline ─────────────────────────────────────────────────────────
def retrieve(query: str, collection_name: str = "policypal", top_k: int = 3) -> list:
    collection = chroma_client.get_collection(collection_name)
    query_embedding = embedder.encode([query]).tolist()
    results = collection.query(query_embeddings=query_embedding, n_results=top_k)

    chunks = results["documents"][0]
    metadatas = results["metadatas"][0]
    distances = results["distances"][0]

    return [
        {
            "chunk": chunk,
            "source": meta["source"],
            "chunk_index": meta["chunk_index"],
            "relevance_score": round(1 - dist, 3)
        }
        for chunk, meta, dist in zip(chunks, metadatas, distances)
    ]


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


def rag_query(query: str, collection_name: str = "policypal") -> dict:
    retrieved = retrieve(query, collection_name)
    answer = generate_answer(query, retrieved)
    return {
        "query": query,
        "answer": answer,
        "sources": [
            {
                "chunk_preview": r["chunk"][:150] + "...",
                "relevance_score": r["relevance_score"]
            }
            for r in retrieved
        ]
    }


# ── Gradio UI ──────────────────────────────────────────────────────────────────
def upload_and_ingest(file):
    if file is None:
        return "❌ Please upload a file"
    result = ingest_document(file.name)
    if "error" in result:
        return f"❌ Error: {result['error']}"
    return f"✅ Ingested successfully!\n📄 File: {result['file']}\n📦 Chunks: {result['chunks']}"


def ask_question(question):
    if not question.strip():
        return "Please enter a question", ""
    try:
        result = rag_query(question)
    except Exception as e:
        return f"❌ Error: {str(e)}", ""
    sources_text = "\n\n".join([
        f"📎 Source {i+1} (relevance: {s['relevance_score']}):\n{s['chunk_preview']}"
        for i, s in enumerate(result["sources"])
    ])
    return result["answer"], sources_text


with gr.Blocks(title="PolicyPal") as demo:
    gr.Markdown("# 📋 PolicyPal — HR Policy Assistant")
    gr.Markdown("Upload your HR policy documents and ask questions in plain English.")

    with gr.Tab("📤 Upload Document"):
        file_input = gr.File(label="Upload PDF, DOCX, or TXT")
        upload_btn = gr.Button("Ingest Document", variant="primary")
        upload_output = gr.Textbox(label="Status", lines=4)
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
        ask_btn.click(ask_question, inputs=question_input, outputs=[answer_output, sources_output])

demo.launch(server_name="0.0.0.0", server_port=7860)
