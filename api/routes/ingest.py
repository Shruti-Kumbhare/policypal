"""
api/routes/ingest.py
────────────────────
Handles document upload and ingestion into the vector store.
"""

import shutil
import tempfile
import os
from fastapi import APIRouter, UploadFile, File
from typing import List

from retrieval.store import ingest_document
from api.schemas.ingest import IngestResponse, FileIngestResult

router = APIRouter()

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt"}


@router.post("/", response_model=IngestResponse)
async def ingest_files(files: List[UploadFile] = File(...)):
    """
    Upload one or more PDF / DOCX / TXT files.
    Each file is saved to a temp path, ingested, then cleaned up.
    """
    results: list[FileIngestResult] = []

    for file in files:
        suffix = os.path.splitext(file.filename)[-1].lower()

        if suffix not in ALLOWED_EXTENSIONS:
            results.append(FileIngestResult(
                file=file.filename,
                error=f"Unsupported file type '{suffix}'. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
            ))
            continue

        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            shutil.copyfileobj(file.file, tmp)
            tmp_path = tmp.name

        try:
            raw = ingest_document(tmp_path, original_filename=file.filename)
            results.append(FileIngestResult(
                file=file.filename,
                chunks_added=raw.get("chunks_added"),
                chunks_skipped=raw.get("chunks_skipped"),
                characters=raw.get("characters"),
                sections_detected=raw.get("sections_detected", []),
                already_ingested=raw.get("already_ingested", False),
            ))
        except Exception as e:
            results.append(FileIngestResult(
                file=file.filename,
                error=str(e)
            ))
        finally:
            os.unlink(tmp_path)

    return IngestResponse(results=results)
