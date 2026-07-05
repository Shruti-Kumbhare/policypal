"""
api/schemas/ingest.py
──────────────────────
Pydantic models for document ingestion endpoints.
"""

from pydantic import BaseModel
from typing import Optional


class FileIngestResult(BaseModel):
    """Result for a single file ingestion attempt."""
    file:              str
    chunks_added:      Optional[int]  = None
    chunks_skipped:    Optional[int]  = None
    characters:        Optional[int]  = None
    sections_detected: list[str]      = []
    already_ingested:  bool           = False
    error:             Optional[str]  = None


class IngestResponse(BaseModel):
    """Response returned after one or more files are ingested."""
    results: list[FileIngestResult]
