import os
import gradio as gr
import PyPDF2
import docx
from sentence_transformers import SentenceTransformer
import chromadb
import torch
from groq import Groq

# ---- Setup ----
device = "cuda" if torch.cuda.is_available() else "cpu"
embedder = SentenceTransformer("all-MiniLM-L6-v2", device=device)
chroma_client = chromadb.Client()
groq_client = Groq(api_key=os.environ["GROQ_API_KEY"])  # from HF Secrets

# ---- Your existing functions (paste them all here) ----
# extract_text(), split_into_chunks(), ingest_document()
# retrieve(), generate_answer(), rag_query()

# ---- Gradio UI ----
def upload_and_ingest(file):
    if file is None:
        return "❌ Please upload a file"
    result = ingest_document(file.name)
    if "error" in result:
        return f"❌ Error: {result['error']}"
    return f"✅ Ingested!\n📄 File: {result['file']}\n📦 Chunks: {result['chunks']}"

def ask_question(question):
    if not question.strip():
        return "Please enter a question", ""
    result = rag_query(question)
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
        question_input = gr.Textbox(label="Your Question", lines=2)
        ask_btn = gr.Button("Ask PolicyPal", variant="primary")
        answer_output = gr.Textbox(label="Answer", lines=5)
        sources_output = gr.Textbox(label="Sources Used", lines=6)
        ask_btn.click(ask_question, inputs=question_input, outputs=[answer_output, sources_output])

demo.launch()
