"""
Banking AI Hackathon - Main FastAPI Application
High-performance async API with multi-agent AI capabilities
"""

import logging
import time
import uuid
from contextlib import asynccontextmanager
from typing import Optional, Union, AsyncGenerator
from datetime import datetime

from fastapi import FastAPI, Request, status, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, Response
from fastapi.encoders import jsonable_encoder
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html
from fastapi.openapi.utils import get_openapi
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.staticfiles import StaticFiles
import uvicorn
from pydantic import BaseModel, Field, AnyHttpUrl
from starlette.middleware.sessions import SessionMiddleware
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.types import ASGIApp, Message

from app.api.v1.api import api_router
from app.api.v1.dependencies import (
    http_exception_handler,
    validation_exception_handler,
    rate_limit_check,
    get_async_db
)
from app.core.config import get_settings, Settings
from app.core.llm_orchestrator import LLMOrchestrator
from app.core.memory_manager import MemoryManager
from app.db.database import Database
from app.schemas.response import (
    ErrorResponse,
    ErrorCode,
    StandardResponse,
    HealthCheckResponse,
    ErrorResponseEnvelope
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
    # Banking AI Hackathon API
    
    High-performance API for the Banking AI System with multi-agent capabilities,
    providing intelligent banking services including transaction analysis, fraud detection,
    and personalized financial recommendations.
    
    ## Authentication
    Most endpoints require authentication using JWT tokens. Obtain a token by logging in.
    
    ## Rate Limiting
    API is rate limited to {settings.RATE_LIMIT} requests per minute per IP address.
    
    ## Error Handling
    All errors follow a consistent format with error codes and human-readable messages.
    """,
    version=settings.API_VERSION,
    docs_url=None,  # We'll serve custom docs
    redoc_url=None,  # We'll serve custom redoc
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    contact={
        "name": "Banking AI Team",
        "email": settings.SUPPORT_EMAIL
    },
    license_info={
        "name": settings.LICENSE_NAME,
        "url": settings.LICENSE_URL
    },
    debug=settings.DEBUG,
    root_path=settings.ROOT_PATH,
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

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For MVP, allow all origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Range", "X-Total-Count", "X-Request-ID", "X-RateLimit-Limit", "X-RateLimit-Remaining"],
)

# Security middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=settings.ALLOWED_HOSTS
)

# Performance middleware
app.add_middleware(
    GZipMiddleware,
    minimum_size=1000,
    compresslevel=6
)

# Session management
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.SECRET_KEY,
    session_cookie=settings.SESSION_COOKIE_NAME,
    max_age=settings.SESSION_LIFETIME,
    same_site=settings.SESSION_SAME_SITE,
    https_only=settings.SESSION_HTTPS_ONLY,
    domain=settings.SESSION_DOMAIN
)

# Request logging middleware
class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for logging HTTP requests and responses."""
    
    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        """Process the request and log details."""
        # Generate or get request ID
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        
        # Log request
        logger.info(
            f"Request: {request.method} {request.url} | "
            f"Headers: {dict(request.headers)} | "
            f"Client: {request.client.host if request.client else 'unknown'}"
        )
        
        # Process request with timing
        start_time = time.time()
        
        try:
            response = await call_next(request)
            process_time = time.time() - start_time
            
            # Log successful response
            logger.info(
                f"Response: {request.method} {request.url} | "
                f"Status: {response.status_code} | "
                f"Time: {process_time:.4f}s | "
                f"Size: {len(response.body) if hasattr(response, 'body') else 0} bytes"
            )
            
            # Add headers
            response.headers["X-Process-Time"] = str(round(process_time * 1000, 2))
            response.headers["X-Request-ID"] = request_id
            
            return response
            
        except Exception as exc:
            process_time = time.time() - start_time
            logger.error(
                f"Error processing {request.method} {request.url} | "
                f"Error: {str(exc)} | "
                f"Time: {process_time:.4f}s",
                f"Process Time: {process_time:.2f}ms",
                exc_info=True
            )
            raise

# Add request logging middleware
app.add_middleware(RequestLoggingMiddleware)

# Rate limiting middleware
class RateLimitMiddleware:
    """Middleware for rate limiting requests."""
    
    async def __call__(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        """Process the request with rate limiting."""
        # Skip rate limiting for health checks and static files
        if any(path in request.url.path for path in ["/health", "/static", "/docs", "/redoc"]):
            return await call_next(request)
        
        # Get client IP
        client_ip = request.client.host if request.client else "unknown"
        
        try:
            # Apply rate limiting
            await rate_limit_check(request)
            
            # Process request
            response = await call_next(request)
            
            # Add rate limit headers
            response.headers["X-RateLimit-Limit"] = str(settings.RATE_LIMIT)
            response.headers["X-RateLimit-Remaining"] = str(
                settings.RATE_LIMIT - 1  # This should come from your rate limiter
            )
            
            return response
            
        except HTTPException as e:
            if e.status_code == 429:  # Rate limit exceeded
                return JSONResponse(
                    status_code=429,
                    headers={
                        "Retry-After": "60",
                        "X-RateLimit-Limit": str(settings.RATE_LIMIT),
                        "X-RateLimit-Remaining": "0"
                    },
                    content={
                        "error": {
                            "code": ErrorCode.RATE_LIMIT_EXCEEDED,
                            "message": "Too many requests, please try again later.",
                            "retry_after": 60
                        }
                    }
                )
            raise

# Add rate limiting middleware
app.add_middleware(RateLimitMiddleware)

# Custom OpenAPI schema
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
        
    openapi_schema = get_openapi(
        title=settings.PROJECT_NAME,
        version=settings.API_VERSION,
        description=app.description,
        routes=app.routes,
    )
    
    # Add security schemes
    openapi_schema["components"]["securitySchemes"] = {
        "OAuth2PasswordBearer": {
            "type": "oauth2",
            "flows": {
                "password": {
                    "tokenUrl": f"{settings.API_V1_STR}/auth/login",
                    "scopes": {
                        "read:profile": "Read your profile",
                        "write:profile": "Update your profile",
                        "read:transactions": "Read your transactions",
                        "write:transactions": "Create/update transactions",
                        "admin": "Admin access"
                    }
                }
            }
        }
    }
    
    # Add security to all endpoints by default
    for path in openapi_schema.get("paths", {}).values():
        for method in path.values():
            # Skip public endpoints
            if path in ["/health", "/auth/login", "/auth/register", "/docs", "/redoc", "/openapi.json"]:
                continue
                
            if "security" not in method:
                method["security"] = [{"OAuth2PasswordBearer": []}]
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

# Apply custom OpenAPI schema
app.openapi = custom_openapi

# Custom docs endpoints
@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    return get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title=f"{app.title} - Swagger UI",
        oauth2_redirect_url=app.swagger_ui_oauth2_redirect_url,
        swagger_js_url="/static/swagger-ui-bundle.js",
        swagger_css_url="/static/swagger-ui.css",
        swagger_favicon_url="/static/favicon.ico",
    )

@app.get("/redoc", include_in_schema=False)
async def redoc_html():
    return get_redoc_html(
        openapi_url=app.openapi_url,
        title=f"{app.title} - ReDoc",
        redoc_js_url="/static/redoc.standalone.js",
    )

# Mount static files for docs
app.mount("/static", StaticFiles(directory="static"), name="static")

# Include API router with version prefix
app.include_router(api_router, prefix=settings.API_V1_STR)

# Health check endpoint with detailed response
@app.get(
    "/health",
    response_model=HealthCheckResponse,
    tags=["System"],
    summary="Health Check",
    description="Check the health status of the API and its dependencies",
    responses={
        200: {
            "description": "Service is healthy",
            "content": {
                "application/json": {
                    "example": {
                        "status": "healthy",
                        "version": "1.0.0",
                        "timestamp": "2023-01-01T00:00:00Z",
                        "dependencies": {
                            "database": "connected",
                            "cache": "connected",
                            "llm_service": "available"
                        }
                    }
                }
            }
        },
        503: {
            "description": "Service is unhealthy",
            "content": {
                "application/json": {
                    "example": {
                        "status": "unhealthy",
                        "version": "1.0.0",
                        "timestamp": "2023-01-01T00:00:00Z",
                        "dependencies": {
                            "database": "error",
                            "cache": "connected",
                            "llm_service": "available"
                        },
                        "errors": ["Database connection failed"]
                    }
                }
            }
        }
    }
)
async def health_check() -> HealthCheckResponse:
    """
    Check the health status of the API and its dependencies.
    
    Returns:
        HealthCheckResponse: The health status of the API.
    """
    dependencies = {}
    errors = []
    
    # Check database connection
    try:
        # Replace with actual database health check
        # await database.execute("SELECT 1")
        dependencies["database"] = "connected"
    except Exception as e:
        logger.error(f"Database health check failed: {str(e)}")
        dependencies["database"] = "error"
        errors.append(f"Database connection failed: {str(e)}")
    
    # Check cache
    try:
        # Replace with actual cache health check
        # await cache.ping()
        dependencies["cache"] = "connected"
    except Exception as e:
        logger.error(f"Cache health check failed: {str(e)}")
        dependencies["cache"] = "error"
        errors.append(f"Cache connection failed: {str(e)}")
    
    # Check LLM service
    try:
        if llm_orchestrator:
            # Replace with actual LLM service health check
            # await llm_orchestrator.health_check()
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
    description="Root endpoint with API information and links",
    responses={
        200: {
            "description": "API information",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "message": "Banking AI API",
                        "data": {
                            "version": "1.0.0",
                            "environment": "development",
                            "docs": "/docs",
                            "health": "/health"
                        }
                    }
                }
            }
        }
    }
)
async def root() -> StandardResponse:
    """
    Root endpoint that returns API information and available endpoints.
    """
    return StandardResponse.success_response(
        message="Banking AI API",
        data={
            "version": settings.API_VERSION,
            "environment": settings.ENVIRONMENT,
            "docs": "/docs",
            "redoc": "/redoc",
            "openapi_schema": "/openapi.json",
            "health": "/health"
        }
    )

def start() -> None:
    """
    Start the application using uvicorn.
    
    This function is used when running the application directly with Python.
    For production, it's recommended to use uvicorn directly.
    """
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        workers=settings.WORKERS,
        log_level=settings.LOG_LEVEL.lower(),
        proxy_headers=settings.PROXY_HEADERS,
        forwarded_allow_ips=settings.FORWARDED_ALLOW_IPS,
        timeout_keep_alive=settings.KEEP_ALIVE_TIMEOUT,
        limit_concurrency=settings.MAX_CONCURRENCY,
        limit_max_requests=settings.MAX_REQUESTS,
        backlog=settings.BACKLOG,
    )

if __name__ == "__main__":
    start()
