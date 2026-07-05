"""
api/schemas/health.py
──────────────────────
Pydantic models for health check endpoint.
"""

from pydantic import BaseModel


class HealthResponse(BaseModel):
    """Health check response."""
    status:  str
    service: str
    version: str
