"""
api/schemas/__init__.py
────────────────────────
Central export for all Pydantic schemas.
Import from here across the codebase:
    from api.schemas import IngestResponse, QueryRequest
"""

from api.schemas.ingest   import FileIngestResult, IngestResponse
from api.schemas.query    import QueryRequest, QueryResponse, SourceItem
from api.schemas.document import DocumentListResponse
from api.schemas.health   import HealthResponse

__all__ = [
    "FileIngestResult",
    "IngestResponse",
    "QueryRequest",
    "QueryResponse",
    "SourceItem",
    "DocumentListResponse",
    "HealthResponse",
]
