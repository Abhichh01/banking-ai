"""
Banking AI Hackathon - Main FastAPI Application
High-performance async API with multi-agent AI capabilities
"""

import logging
import uuid
from contextlib import asynccontextmanager
from typing import Optional, AsyncGenerator
from datetime import datetime

from fastapi import FastAPI, Request, status, HTTPException, Depends, BackgroundTasks
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.openapi.utils import get_openapi
import uvicorn

from app.api.v1.api import api_router
from app.api.v1.dependencies import (
    http_exception_handler,
    validation_exception_handler,
    get_async_db
)
from app.core.config import get_settings, Settings
from app.core.llm_orchestrator import LLMOrchestrator
from app.core.memory_manager import MemoryManager
from app.db.database import Database
from app.schemas.response import (
    ErrorCode,
    StandardResponse,
    HealthCheckResponse
)
from app.schemas.token import Token, TokenData

# Get application settings
settings: Settings = get_settings()

# Configure logging
logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Global instances
db = Database()
llm_orchestrator: Optional[LLMOrchestrator] = None
memory_manager: Optional[MemoryManager] = None

# Application lifespan management
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Manage application startup and shutdown events with async context manager.
    
    This function handles:
    - Core component initialization
    - Database connection setup
    - Clean shutdown procedures
    """
    global llm_orchestrator, memory_manager
    
    # Startup sequence
    logger.info("🚀 Starting Banking AI System...")
    
    try:
        # Initialize core components
        logger.info("Initializing core components...")
        llm_orchestrator = await LLMOrchestrator.create()
        memory_manager = await MemoryManager.create()
        
        # Initialize database connections
        logger.info("Initializing database connections...")
        async with db.async_engine.begin() as conn:
            await conn.run_sync(lambda conn: logger.info("Database connection established"))
        
        logger.info("✅ Application startup complete")
        
        # Yield control back to FastAPI
        yield
        
    except Exception as e:
        logger.error(f"❌ Error during application startup: {str(e)}", exc_info=True)
        raise
        
    finally:
        # Shutdown sequence
        logger.info("🛑 Shutting down Banking AI System...")
        
        try:
            # Clean up resources
            if memory_manager:
                await memory_manager.close()
            if db.async_engine:
                await db.async_engine.dispose()
        except Exception as e:
            logger.error(f"Error during shutdown: {str(e)}", exc_info=True)
        
        logger.info("✅ Application shutdown complete")

# Create FastAPI application with lifespan management
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="""
    # Banking AI Hackathon API - MVP
    
    High-performance API for the Banking AI System focused on behavioral pattern analysis,
    user authentication, and financial recommendations.
    """,
    version=settings.API_VERSION,
    lifespan=lifespan
)

# Custom exception handlers
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)

@app.exception_handler(500)
async def internal_server_error_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle 500 errors with consistent error format."""
    logger.error(f"Internal server error: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": ErrorCode.INTERNAL_SERVER_ERROR,
                "message": "Internal server error",
                "details": str(exc) if settings.DEBUG else None
            }
        }
    )

@app.exception_handler(404)
async def not_found_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handle 404 errors with consistent error format."""
    return JSONResponse(
        status_code=404,
        content={
            "error": {
                "code": ErrorCode.NOT_FOUND,
                "message": "The requested resource was not found"
            }
        }
    )

# Simple request logging
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Simple logging middleware for requests."""
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    
    # Log basic request info
    logger.info(f"Request: {request.method} {request.url}")
    
    # Process request
    response = await call_next(request)
    
    # Log response status
    logger.info(f"Response: {request.method} {request.url} | Status: {response.status_code}")
    
    # Add request ID header
    response.headers["X-Request-ID"] = request_id
    
    return response

# Custom OpenAPI schema with security
@app.on_event("startup")
async def customize_openapi():
    """Add security schemes to OpenAPI schema."""
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    
    # Add security schemes
    if "components" not in openapi_schema:
        openapi_schema["components"] = {}
        
    openapi_schema["components"]["securitySchemes"] = {
        "bearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT"
        }
    }
    
    app.openapi_schema = openapi_schema

# Include API router with version prefix
app.include_router(api_router, prefix=settings.API_V1_STR)

# Health check endpoint
@app.get(
    "/health",
    response_model=HealthCheckResponse,
    tags=["System"],
    summary="Health Check",
    description="Check the health status of the API and its dependencies"
)
async def health_check() -> HealthCheckResponse:
    """Check the health status of the API and its dependencies."""
    dependencies = {}
    errors = []
    
    # Check database connection
    try:
        async with db.async_engine.begin() as conn:
            await conn.execute("SELECT 1")
        dependencies["database"] = "connected"
    except Exception as e:
        logger.error(f"Database health check failed: {str(e)}")
        dependencies["database"] = "error"
        errors.append(f"Database connection failed: {str(e)}")
    
    # Check LLM service
    try:
        if llm_orchestrator:
            dependencies["llm_service"] = "available"
        else:
            dependencies["llm_service"] = "not_initialized"
    except Exception as e:
        logger.error(f"LLM service health check failed: {str(e)}")
        dependencies["llm_service"] = "unavailable"
        errors.append(f"LLM service check failed: {str(e)}")
    
    status = "healthy" if not errors else "unhealthy"
    
    return HealthCheckResponse(
        status=status,
        version=settings.API_VERSION,
        timestamp=datetime.utcnow(),
        dependencies=dependencies,
        errors=errors if errors else None
    )

# Root endpoint
@app.get(
    "/",
    response_model=StandardResponse,
    tags=["System"],
    summary="API Root",
    description="Root endpoint with API information"
)
async def root() -> StandardResponse:
    """Root endpoint with API information."""
    return StandardResponse.success_response(
        message="Banking AI API - MVP",
        data={
            "version": settings.API_VERSION,
            "docs": "/docs",
            "health": "/health"
        }
    )

def start() -> None:
    """Start the application using uvicorn."""
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        workers=1,  # Simplified for MVP
        log_level=settings.LOG_LEVEL.lower()
    )

if __name__ == "__main__":
    start()
