import gradio as gr
from retrieval.store import ingest_document
from retrieval.retriever import retrieve
from generation.generator import generate_answer


# ── Handlers ───────────────────────────────────────────────────────────────────

def upload_and_ingest(files):
    if not files:
        return "❌ Please upload at least one file."

    results = []
    for file in files:
        result = ingest_document(file.name)

        if "error" in result:
            results.append(f"❌ {file.name.split('/')[-1]}: {result['error']}")

        elif result.get("already_ingested"):
            results.append(f"⚠️  {file.name.split('/')[-1]} — already ingested, skipped.")

        else:
            sections_preview = ", ".join(result["sections_detected"]) or "none detected"
            results.append(
                f"✅ {file.name.split('/')[-1]}\n"
                f"   📦 Chunks added : {result['chunks_added']}\n"
                f"   🔤 Characters   : {result['characters']}\n"
                f"   📑 Sections     : {sections_preview}"
            )

    return "\n\n".join(results)


def ask_question(question):
    if not question.strip():
        return "Please enter a question.", ""

    try:
        retrieved = retrieve(question)

        if not retrieved:
            return (
                "⚠️ No relevant content found above the confidence threshold.\n"
                "Try rephrasing your question, or check that the right documents are uploaded.",
                "",
            )

        answer = generate_answer(question, retrieved)

        sources_text = "\n\n".join([
            f"📎 [{r['relevance_score']}] {r['source_name']} — {r['section']}\n"
            f"{r['chunk'][:180]}..."
            for r in retrieved
        ])

        return answer, sources_text

    except Exception as e:
        return f"❌ Error: {str(e)}", ""


# ── UI ─────────────────────────────────────────────────────────────────────────

with gr.Blocks(title="PolicyPal", theme=gr.themes.Soft()) as demo:
    gr.Markdown("# 📋 PolicyPal — HR Policy Assistant")
    gr.Markdown("Upload HR policy documents and ask questions in plain English.")

    with gr.Tab("📤 Upload Documents"):
        file_input = gr.File(
            label="Upload PDF, DOCX, or TXT files",
            file_count="multiple",
        )
        upload_btn = gr.Button("Ingest Documents", variant="primary")
        upload_output = gr.Textbox(label="Ingestion Status", lines=8)
        upload_btn.click(upload_and_ingest, inputs=file_input, outputs=upload_output)

    with gr.Tab("💬 Ask Questions"):
        question_input = gr.Textbox(
            label="Your Question",
            placeholder="e.g. How many sick leaves do I get per year?",
            lines=2,
        )
        ask_btn = gr.Button("Ask PolicyPal", variant="primary")
        answer_output = gr.Textbox(label="Answer", lines=6)
        sources_output = gr.Textbox(label="Sources Used", lines=8)
        ask_btn.click(
            ask_question,
            inputs=question_input,
            outputs=[answer_output, sources_output],
        )

demo.launch(share=True)
