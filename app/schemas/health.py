"""
Health check schemas.
"""

from datetime import datetime
from pydantic import BaseModel

class HealthCheck(BaseModel):
    """Health check response model."""
    status: str
    version: str
    timestamp: str
    environment: str
    debug: bool
