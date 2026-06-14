import re
from config import CHUNK_SIZE, CHUNK_OVERLAP


# Matches headings like:
#   "1. Purpose", "2.1 Leave Types", "Section 3 - Attendance"
#   "SECTION 4:", "Chapter 5", "A. Introduction"
SECTION_PATTERN = re.compile(
    r"^(?:"
    r"\d+(?:\.\d+)*[\.\)]\s+"       # 1. / 1.1. / 1.1.2.
    r"|Section\s+\d+[\.\:\-\s]"     # Section 3 / Section 3:
    r"|Chapter\s+\d+"               # Chapter 5
    r"|[A-Z]\.\s+"                  # A. / B.
    r")",
    re.IGNORECASE | re.MULTILINE,
)


def _word_chunks(text: str, chunk_size: int, overlap: int) -> list[dict]:
    """Fallback: fixed word-count chunking (same as v1)."""
    words = text.split()
    chunks = []
    for i in range(0, len(words), chunk_size - overlap):
        chunk = " ".join(words[i : i + chunk_size])
        if chunk:
            chunks.append({"text": chunk, "section": "unknown", "section_index": i})
    return chunks


def _section_chunks(text: str) -> list[dict]:
    """
    Split text on section headings.
    Each chunk = one section (heading + body).
    Carries section title and index as metadata.
    """
    lines = text.splitlines()
    sections = []
    current_title = "preamble"
    current_lines = []

    for line in lines:
        if SECTION_PATTERN.match(line.strip()):
            if current_lines:
                sections.append((current_title, "\n".join(current_lines).strip()))
            current_title = line.strip()
            current_lines = [line]
        else:
            current_lines.append(line)

    if current_lines:
        sections.append((current_title, "\n".join(current_lines).strip()))

    chunks = []
    for idx, (title, body) in enumerate(sections):
        if not body:
            continue
        # If a single section is very long, sub-chunk it by words
        words = body.split()
        if len(words) <= CHUNK_SIZE:
            chunks.append({"text": body, "section": title, "section_index": idx})
        else:
            sub = _word_chunks(body, CHUNK_SIZE, CHUNK_OVERLAP)
            for s in sub:
                s["section"] = title
                s["section_index"] = idx
            chunks.extend(sub)

    return chunks


def chunk_text(text: str) -> list[dict]:
    """
    Auto-detect whether the document has numbered sections.
    Returns list of dicts: {text, section, section_index}
    """
    section_hits = len(SECTION_PATTERN.findall(text))

    if section_hits >= 3:
        chunks = _section_chunks(text)
        if chunks:
            return chunks

    # Fallback to word-count chunking for unstructured docs
    return _word_chunks(text, CHUNK_SIZE, CHUNK_OVERLAP)
