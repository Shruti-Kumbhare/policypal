import os
import requests
import gradio as gr

# In HuggingFace Spaces, FastAPI runs on port 7861 alongside Gradio on 7860
API_BASE = os.environ.get("API_BASE_URL", "http://localhost:7861")


# ── Handlers ───────────────────────────────────────────────────────────────────

def upload_and_ingest(files):
    if not files:
        return "❌ Please upload at least one file."

    file_tuples = [("files", (f.name.split("/")[-1], open(f.name, "rb"))) for f in files]

    try:
        resp = requests.post(f"{API_BASE}/ingest/", files=file_tuples, timeout=120)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        return f"❌ API error: {e}"

    lines = []
    for r in data["results"]:
        if "error" in r:
            lines.append(f"❌ {r['file']}: {r['error']}")
        elif r.get("already_ingested"):
            lines.append(f"⚠️  {r['file']} — already ingested, skipped")
        else:
            sections = ", ".join(r.get("sections_detected", [])) or "none detected"
            lines.append(
                f"✅ {r['file']}\n"
                f"   📦 Chunks: {r['chunks_added']} | 🔤 Chars: {r['characters']}\n"
                f"   📑 Sections: {sections}"
            )
    return "\n\n".join(lines)


def ask_question(question):
    if not question.strip():
        return "Please enter a question.", ""

    try:
        resp = requests.post(
            f"{API_BASE}/query/",
            json={"question": question},
            timeout=60,
        )
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        return f"❌ API error: {e}", ""

    sources_text = "\n\n".join([
        f"📎 [{s['relevance_score']}] {s['source_name']} — {s['section']}\n{s['excerpt']}..."
        for s in data["sources"]
    ])

    return data["answer"], sources_text


def list_docs():
    try:
        resp = requests.get(f"{API_BASE}/documents/", timeout=10)
        data = resp.json()
        if not data["documents"]:
            return "No documents ingested yet."
        return "\n".join([f"📄 {d}" for d in data["documents"]])
    except Exception as e:
        return f"❌ {e}"


# ── UI ─────────────────────────────────────────────────────────────────────────

with gr.Blocks(title="PolicyPal") as demo:
    gr.Markdown("# 📋 PolicyPal — HR Policy Assistant")
    gr.Markdown("Upload HR policy documents and ask questions in plain English.")

    with gr.Tab("📤 Upload Documents"):
        file_input = gr.File(label="Upload PDF, DOCX, or TXT", file_count="multiple")
        upload_btn = gr.Button("Ingest Documents", variant="primary")
        upload_output = gr.Textbox(label="Status", lines=8)
        upload_btn.click(upload_and_ingest, inputs=file_input, outputs=upload_output)

    with gr.Tab("💬 Ask Questions"):
        question_input = gr.Textbox(
            label="Your Question",
            placeholder="e.g. How many sick leaves do I get per year?",
            lines=2,
        )
        ask_btn = gr.Button("Ask PolicyPal", variant="primary")
        answer_output  = gr.Textbox(label="Answer", lines=6)
        sources_output = gr.Textbox(label="Sources Used", lines=8)
        ask_btn.click(ask_question, inputs=question_input, outputs=[answer_output, sources_output])

    with gr.Tab("📂 Loaded Documents"):
        refresh_btn = gr.Button("Refresh", variant="secondary")
        docs_output = gr.Textbox(label="Ingested documents", lines=10)
        refresh_btn.click(list_docs, inputs=[], outputs=docs_output)

demo.launch(server_port=7860, theme=gr.themes.Soft())
