"""
Merchant schemas for request/response validation and serialization.
"""
from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum
from pydantic import BaseModel, Field, HttpUrl, validator, confloat, conint
from uuid import UUID

from app.schemas.response import StandardResponse, PaginatedResponse


class MerchantCategory(str, Enum):
    """Merchant categories for classification."""
    RETAIL = "retail"
    GROCERY = "grocery"
    RESTAURANT = "restaurant"
    TRAVEL = "travel"
    TRANSPORT = "transport"
    UTILITIES = "utilities"
    ENTERTAINMENT = "entertainment"
    HEALTHCARE = "healthcare"
    EDUCATION = "education"
    FINANCIAL = "financial"
    GOVERNMENT = "government"
    OTHER = "other"


class MerchantStatus(str, Enum):
    """Merchant account status."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    UNDER_REVIEW = "under_review"


class MerchantBase(BaseModel):
    """Base schema for merchant with common fields."""
    name: str = Field(..., min_length=1, max_length=200, description="Legal business name")
    category: MerchantCategory = Field(..., description="Primary business category")
    mcc_code: str = Field(..., min_length=4, max_length=4, description="Merchant Category Code (MCC)")
    description: Optional[str] = Field(None, max_length=1000, description="Business description")
    website: Optional[HttpUrl] = Field(None, description="Business website URL")
    phone: Optional[str] = Field(None, pattern=r'^\+?[1-9]\d{1,14}$', description="Business phone number in E.164 format")
    email: Optional[str] = Field(None, pattern=r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', 
                               description="Business contact email")
    
    # Location Information
    address_line1: Optional[str] = Field(None, max_length=200, description="Street address line 1")
    address_line2: Optional[str] = Field(None, max_length=200, description="Street address line 2")
    city: Optional[str] = Field(None, max_length=100, description="City")
    state: Optional[str] = Field(None, max_length=100, description="State/Province/Region")
    postal_code: Optional[str] = Field(None, max_length=20, description="Postal/ZIP code")
    country: str = Field("India", max_length=100, description="Country name")
    latitude: Optional[float] = Field(None, ge=-90, le=90, description="Geographic latitude")
    longitude: Optional[float] = Field(None, ge=-180, le=180, description="Geographic longitude")
    
    # Business Information
    business_type: Optional[str] = Field(None, max_length=100, description="Type of business entity")
    business_registration_number: Optional[str] = Field(
        None, 
        max_length=100, 
        description="Official business registration number"
    )
    tax_id: Optional[str] = Field(None, max_length=100, description="Tax identification number")
    
    class Config:
        schema_extra = {
            "example": {
                "name": "Example Merchant Inc.",
                "category": "retail",
                "mcc_code": "5734",
                "description": "Leading electronics retailer",
                "website": "https://example.com",
                "phone": "+919876543210",
                "email": "contact@example.com",
                "address_line1": "123 Business Street",
                "city": "Mumbai",
                "state": "Maharashtra",
                "postal_code": "400001",
                "country": "India",
                "latitude": 19.0760,
                "longitude": 72.8777,
                "business_type": "Private Limited Company",
                "business_registration_number": "U74999MH2010PTC123456",
                "tax_id": "27AABCE1234F1Z5"
            }
        }


class MerchantCreate(MerchantBase):
    """Schema for creating a new merchant."""
    created_by: str = Field(..., description="ID of the user creating this merchant")
    
    @validator('mcc_code')
    def validate_mcc_code(cls, v):
        if not v.isdigit():
            raise ValueError("MCC code must be a 4-digit number")
        return v


class MerchantUpdate(BaseModel):
    """Schema for updating an existing merchant."""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    category: Optional[MerchantCategory] = None
    mcc_code: Optional[str] = Field(None, min_length=4, max_length=4)
    description: Optional[str] = Field(None, max_length=1000)
    website: Optional[HttpUrl] = None
    phone: Optional[str] = Field(None, pattern=r'^\+?[1-9]\d{1,14}$')
    email: Optional[str] = Field(None, pattern=r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    address_line1: Optional[str] = Field(None, max_length=200)
    address_line2: Optional[str] = Field(None, max_length=200)
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=100)
    postal_code: Optional[str] = Field(None, max_length=20)
    country: Optional[str] = Field(None, max_length=100)
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    business_type: Optional[str] = Field(None, max_length=100)
    business_registration_number: Optional[str] = Field(None, max_length=100)
    tax_id: Optional[str] = Field(None, max_length=100)
    status: Optional[MerchantStatus] = None
    is_high_risk: Optional[bool] = None
    risk_score: Optional[float] = Field(None, ge=0, le=1)
    
    class Config:
        schema_extra = {
            "example": {
                "name": "Updated Merchant Name",
                "category": "retail",
                "status": "active"
            }
        }


class MerchantInDBBase(MerchantBase):
    """Base schema for merchant data stored in the database."""
    merchant_id: str = Field(..., description="Unique merchant identifier")
    status: MerchantStatus = Field(default=MerchantStatus.ACTIVE, description="Current status of the merchant")
    risk_score: float = Field(default=0.0, ge=0, le=1, description="Risk assessment score (0-1)")
    is_high_risk: bool = Field(default=False, description="Flag for high-risk merchants")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Record creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional merchant metadata")
    
    class Config:
        orm_mode = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }


class Merchant(MerchantInDBBase):
    """Schema for returning merchant data (public view)."""
    pass


class MerchantInDB(MerchantInDBBase):
    """Schema for internal merchant data with audit fields."""
    created_by: str = Field(..., description="ID of the user who created this merchant")
    updated_by: str = Field(..., description="ID of the user who last updated this merchant")
    last_reviewed: Optional[datetime] = Field(None, description="Timestamp of last review")
    reviewed_by: Optional[str] = Field(None, description="ID of the user who last reviewed this merchant")


class MerchantResponse(StandardResponse):
    """Response schema for single merchant."""
    data: Merchant


class MerchantListResponse(PaginatedResponse):
    """Response schema for paginated list of merchants."""
    data: List[Merchant]


class MerchantCategoryStats(BaseModel):
    """Statistics for merchant categories."""
    category: MerchantCategory
    count: int = Field(..., ge=0, description="Number of merchants in this category")
    total_transactions: int = Field(..., ge=0, description="Total number of transactions")
    total_amount: float = Field(..., ge=0, description="Total transaction amount in base currency")
    average_transaction: float = Field(..., ge=0, description="Average transaction amount")


class MerchantSearchFilter(BaseModel):
    """Filter criteria for searching merchants."""
    name: Optional[str] = Field(None, description="Filter by merchant name (partial match)")
    category: Optional[MerchantCategory] = Field(None, description="Filter by merchant category")
    status: Optional[MerchantStatus] = Field(None, description="Filter by merchant status")
    city: Optional[str] = Field(None, description="Filter by city")
    state: Optional[str] = Field(None, description="Filter by state/region")
    country: Optional[str] = Field(None, description="Filter by country")
    min_risk_score: Optional[float] = Field(None, ge=0, le=1, description="Minimum risk score")
    max_risk_score: Optional[float] = Field(None, ge=0, le=1, description="Maximum risk score")
    is_high_risk: Optional[bool] = Field(None, description="Filter by high-risk status")
    created_after: Optional[datetime] = Field(None, description="Filter merchants created after this date")
    created_before: Optional[datetime] = Field(None, description="Filter merchants created before this date")
    
    class Config:
        schema_extra = {
            "example": {
                "category": "retail",
                "status": "active",
                "min_risk_score": 0.0,
                "max_risk_score": 0.5
            }
        }
