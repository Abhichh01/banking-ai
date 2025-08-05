"""
Health Check Endpoint

This module provides health check endpoints to monitor the status of the API.
"""

from datetime import datetime

from fastapi import APIRouter

from app.core.config import get_settings
from app.schemas.health import HealthCheck

# Get settings
settings = get_settings()

router = APIRouter()

@router.get("/health", response_model=HealthCheck)
async def health_check() -> HealthCheck:
    """
    Health check endpoint.
    
    Returns:
        HealthCheck: The health status of the API.
    """
    return HealthCheck(
        status="healthy",
        version=settings.VERSION,
        timestamp=datetime.utcnow().isoformat(),
        environment=settings.ENVIRONMENT,
        debug=settings.DEBUG
    )
