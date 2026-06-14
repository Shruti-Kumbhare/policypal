from groq import Groq
from config import GROQ_API_KEY, GROQ_MODEL, MAX_TOKENS, TEMPERATURE


_client = Groq(api_key=GROQ_API_KEY)
print("✅ Groq client ready")


SYSTEM_PROMPT = """You are PolicyPal, a precise and helpful HR policy assistant.
Answer questions using ONLY the context provided.
Always cite the section name and document you are referencing.
If the answer is not in the context, say exactly: "I couldn't find that in the uploaded documents." """


def generate_answer(query: str, retrieved_chunks: list[dict]) -> str:
    """Build context from retrieved chunks and call Groq LLM."""
    context_parts = []
    for r in retrieved_chunks:
        context_parts.append(
            f"[Source: {r['source_name']} | Section: {r['section']}]\n{r['chunk']}"
        )
    context = "\n\n---\n\n".join(context_parts)

    user_message = f"""Context:
{context}

Question: {query}

Answer (cite section and document):"""

    response = _client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
        temperature=TEMPERATURE,
        max_tokens=MAX_TOKENS,
    )
    return response.choices[0].message.content
