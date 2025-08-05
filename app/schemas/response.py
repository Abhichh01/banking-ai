"""
Response schemas for consistent API responses.
"""
from typing import Generic, TypeVar, Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field, validator

# Generic type for response data
T = TypeVar('T')

class StandardResponse(BaseModel):
    """Standard response schema for simple success/error messages."""
    success: bool = Field(..., description="Indicates if the request was successful")
    message: Optional[str] = Field(None, description="Human-readable message")
    data: Optional[Dict[str, Any]] = Field(None, description="Response data")

    @classmethod
    def success_response(cls, message: str = "Operation completed successfully", data: Optional[Dict[str, Any]] = None):
        """Create a success response."""
        return cls(success=True, message=message, data=data or {})
    
    @classmethod
    def error_response(cls, message: str = "An error occurred", data: Optional[Dict[str, Any]] = None):
        """Create an error response."""
        return cls(success=False, message=message, data=data or {})

class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response with metadata"""
    items: List[T] = Field(..., description="List of items")
    total: int = Field(..., description="Total number of items")
    page: int = Field(..., description="Current page number (1-based)")
    per_page: int = Field(..., description="Number of items per page")
    pages: int = Field(..., description="Total number of pages")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }

class ErrorCode(str, Enum):
    """Standard error codes for consistent error responses."""
    # Authentication & Authorization
    UNAUTHORIZED = "unauthorized"
    FORBIDDEN = "forbidden"
    INVALID_CREDENTIALS = "invalid_credentials"
    TOKEN_EXPIRED = "token_expired"
    INVALID_TOKEN = "invalid_token"
    INSUFFICIENT_PERMISSIONS = "insufficient_permissions"
    ACCOUNT_DISABLED = "account_disabled"
    
    # Validation
    VALIDATION_ERROR = "validation_error"
    INVALID_INPUT = "invalid_input"
    MISSING_REQUIRED_FIELD = "missing_required_field"
    INVALID_FORMAT = "invalid_format"
    
    # Resources
    NOT_FOUND = "not_found"
    ALREADY_EXISTS = "already_exists"
    CONFLICT = "conflict"
    
    # Rate Limiting
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    
    # Server
    INTERNAL_SERVER_ERROR = "internal_server_error"
    SERVICE_UNAVAILABLE = "service_unavailable"
    
    # Business Logic
    INSUFFICIENT_FUNDS = "insufficient_funds"
    TRANSACTION_LIMIT_EXCEEDED = "transaction_limit_exceeded"
    INVALID_OPERATION = "invalid_operation"

class ErrorResponse(BaseModel):
    """Standard error response schema."""
    code: ErrorCode = Field(..., description="Error code")
    message: str = Field(..., description="Human-readable error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")

class ValidationErrorDetail(BaseModel):
    """Validation error detail schema."""
    field: str = Field(..., description="Field that failed validation")
    code: str = Field(..., description="Validation error code")
    message: str = Field(..., description="Validation error message")
    value: Optional[Any] = Field(None, description="Value that failed validation")

class ValidationErrorResponse(ErrorResponse):
    """Validation error response schema."""
    errors: List[ValidationErrorDetail] = Field(..., description="List of validation errors")

class SuccessResponse(BaseModel, Generic[T]):
    """Generic success response with data payload"""
    success: bool = Field(True, description="Indicates successful operation")
    data: T = Field(..., description="Response data")
    message: Optional[str] = Field(None, description="Optional success message")

class EmptyResponse(SuccessResponse[None]):
    """Success response with no data."""
    data: None = None

class HealthCheckResponse(BaseModel):
    """Health check response schema."""
    status: str = Field(..., description="Service status")
    version: str = Field(..., description="API version")
    timestamp: datetime = Field(..., description="Server timestamp")
    dependencies: Dict[str, str] = Field(..., description="Dependency statuses")

class PaginationLinks(BaseModel):
    """Pagination links for API responses."""
    self: str = Field(..., description="Link to the current page")
    first: str = Field(..., description="Link to the first page")
    prev: Optional[str] = Field(None, description="Link to the previous page")
    next: Optional[str] = Field(None, description="Link to the next page")
    last: str = Field(..., description="Link to the last page")

class ListResponse(BaseModel, Generic[T]):
    """Generic list response with items"""
    items: List[T] = Field(..., description="List of items")
    total: int = Field(..., description="Total number of items")

class BulkOperationResult(BaseModel):
    """Result of a bulk operation."""
    total: int = Field(..., description="Total number of items")
    processed: int = Field(..., description="Number of items processed")
    successful: int = Field(..., description="Number of successful operations")
    failed: int = Field(..., description="Number of failed operations")
    errors: Optional[List[Dict[str, Any]]] = Field(None, description="List of errors")

class StatusResponse(BaseModel):
    """Status response for asynchronous operations."""
    id: str = Field(..., description="Operation ID")
    status: str = Field(..., description="Operation status")
    progress: Optional[float] = Field(None, description="Progress percentage (0-100)")
    result: Optional[Dict[str, Any]] = Field(None, description="Operation result")
    created_at: datetime = Field(..., description="When the operation was created")
    updated_at: datetime = Field(..., description="When the operation was last updated")

class ErrorResponseEnvelope(BaseModel):
    """Wrapper for error responses to match standard format."""
    error: ErrorResponse = Field(..., description="Error details")

class ValidationErrorEnvelope(BaseModel):
    """Wrapper for validation error responses."""
    error: ValidationErrorResponse = Field(..., description="Validation error details")
