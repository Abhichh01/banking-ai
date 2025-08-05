"""
Base schema mixins and utilities
"""
from datetime import datetime
from typing import Any, Dict, Optional, TypeVar, Generic, List
from pydantic import BaseModel, Field, field_validator

T = TypeVar('T')

class BaseSchema(BaseModel):
    """Base schema with common fields and configuration"""
    model_config = {
        "from_attributes": True,
        "json_encoders": {
            datetime: lambda v: v.isoformat(),
        },
        "arbitrary_types_allowed": True
    }

class TimestampMixin(BaseModel):
    """
    Mixin for timestamp fields
    """
    created_at: Optional[datetime] = Field(
        None, description="Timestamp when the record was created"
    )
    updated_at: Optional[datetime] = Field(
        None, description="Timestamp when the record was last updated"
    )

    @field_validator('created_at', 'updated_at', mode='before')
    def set_dates(cls, v):
        if v is None:
            return datetime.now(datetime.timezone.utc)
        if isinstance(v, str):
            return datetime.fromisoformat(v)
        return v

class IDSchemaMixin(BaseModel):
    """Mixin for ID field validation"""
    id: int = Field(..., gt=0, description="Unique identifier")

class PaginationSchema(BaseModel):
    """Pagination query parameters"""
    page: int = Field(1, ge=1, description="Page number")
    page_size: int = Field(10, ge=1, le=100, description="Items per page")

class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response schema."""
    items: List[T] = Field(..., description="Page items")
    total: int = Field(..., description="Total number of items")
    page: int = Field(..., description="Current page number")
    size: int = Field(..., description="Page size")
    pages: int = Field(..., description="Total number of pages")

class ErrorResponse(BaseModel):
    """Standard error response"""
    detail: str = Field(..., description="Error message")
    code: str = Field(..., description="Error code")
    status_code: int = Field(..., description="HTTP status code")
    meta: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")
