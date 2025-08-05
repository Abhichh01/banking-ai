"""
User-related Pydantic schemas for request/response validation.
"""
from datetime import date, datetime, timezone
from typing import Optional, List, Dict, Any, Union, Annotated
from pydantic import field_validator, model_validator
from pydantic import BaseModel, EmailStr, Field, HttpUrl, conint, constr, condecimal
from enum import Enum

from .base import BaseSchema, TimestampMixin, IDSchemaMixin

# Enums (aligned with models)
class UserRole(str, Enum):
    CUSTOMER = "customer"
    AGENT = "agent"
    MANAGER = "manager"
    ADMIN = "admin"
    SYSTEM = "system"
    FRAUD_ANALYST = "fraud_analyst"
    CUSTOMER_SERVICE = "customer_service"
    FINANCIAL_ADVISOR = "financial_advisor"

class UserStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING_VERIFICATION = "pending_verification"

class CustomerSegment(str, Enum):
    RETAIL = "retail"
    PREMIUM = "premium"
    PRIVATE = "private"
    BUSINESS = "business"
    WEALTH = "wealth"
    CORPORATE = "corporate"
    STUDENT = "student"
    SENIOR = "senior"
    YOUNG_ADULT = "young_adult"

class RiskProfile(str, Enum):
    CONSERVATIVE = "conservative"
    MODERATE = "moderate"
    BALANCED = "balanced"
    GROWTH = "growth"
    AGGRESSIVE = "aggressive"
    NOT_ASSESSED = "not_assessed"

class KYCStatus(str, Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    VERIFIED = "verified"
    PENDING_VERIFICATION = "pending_verification"
    REJECTED = "rejected"
    EXPIRED = "expired"

class MFAMethod(str, Enum):
    SMS = "sms"
    EMAIL = "email"
    TOTP = "totp"
    AUTHENTICATOR = "authenticator"
    HARDWARE_KEY = "hardware_key"

class Gender(str, Enum):
    MALE = "male"
    FEMALE = "female"
    NON_BINARY = "non_binary"
    OTHER = "other"
    PREFER_NOT_TO_SAY = "prefer_not_to_say"

class EmploymentStatus(str, Enum):
    EMPLOYED = "employed"
    SELF_EMPLOYED = "self_employed"
    UNEMPLOYED = "unemployed"
    RETIRED = "retired"
    STUDENT = "student"
    HOMEMAKER = "homemaker"

# Shared properties
class UserBase(BaseModel):
    """Base schema for user data shared between create/update operations."""
    customer_number: Optional[str] = Field(
        None,
        min_length=6,
        max_length=50,
        description="Unique identifier for the customer in the banking system",
        example="CUST123456"
    )
    email: Optional[EmailStr] = Field(
        None,
        description="Primary email address for communication",
        example="user@example.com"
    )
    phone_number: Optional[str] = Field(
        None,
        min_length=10,
        max_length=20,
        pattern=r'^\+?[1-9]\d{1,14}$',  # E.164 format
        description="Primary contact number with country code",
        example="+919876543210"
    )
    first_name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Legal first name of the user"
    )
    middle_name: Optional[str] = Field(
        None,
        max_length=100,
        description="Middle name or initial if applicable"
    )
    last_name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Legal last name or family name"
    )
    date_of_birth: date = Field(
        ...,
        description="Date of birth for age verification and KYC"
    )
    gender: Optional[Gender] = Field(
        None,
        description="Self-identified gender"
    )
    preferred_language: str = Field(
        "en",
        min_length=2,
        max_length=10,
        description="Preferred language for communication (ISO 639-1 code)",
        example="en"
    )
    timezone: str = Field(
        "UTC",
        description="User's preferred timezone",
        example="America/New_York"
    )
    profile_picture_url: Optional[HttpUrl] = Field(
        None,
        description="URL to the user's profile picture"
    )
    signature_url: Optional[HttpUrl] = Field(
        None,
        description="URL to the user's digital signature"
    )
    customer_segment: CustomerSegment = Field(
        CustomerSegment.RETAIL,
        description="Customer segmentation for targeted services"
    )
    risk_profile: RiskProfile = Field(
        RiskProfile.NOT_ASSESSED,
        description="User's risk profile for investment and credit decisions"
    )
    kyc_status: KYCStatus = Field(
        KYCStatus.NOT_STARTED,
        description="KYC verification status"
    )
    credit_score: Optional[int] = Field(
        None,
        ge=300,
        le=850,
        description="User's credit score (300-850)"
    )
    annual_income: Optional[float] = Field(
        None,
        description="Annual income in the account's currency"
    )
    net_worth: Optional[float] = Field(
        None,
        description="Estimated net worth in the account's currency"
    )
    role: UserRole = Field(
        UserRole.CUSTOMER,
        description="User role for access control and permissions"
    )
    status: UserStatus = Field(
        UserStatus.PENDING_VERIFICATION,
        description="Current account status"
    )
    employment_status: Optional[EmploymentStatus] = Field(
        None,
        description="Current employment status"
    )
    employer_name: Optional[str] = Field(
        None,
        max_length=200,
        description="Current employer/organization name"
    )
    job_title: Optional[str] = Field(
        None,
        max_length=200,
        description="Current job title/position"
    )
    industry: Optional[str] = Field(
        None,
        max_length=100,
        description="Industry/sector of employment"
    )
    occupation: Optional[str] = Field(
        None,
        max_length=100,
        description="Professional occupation category"
    )
    
    model_config = {
        "json_encoders": {datetime: lambda v: v.isoformat() if v else None},
        "json_schema_extra": {
            "example": {
                "customer_number": "CUST123456",
                "email": "user@example.com",
                "phone_number": "+919876543210",
                "first_name": "John",
                "middle_name": "William",
                "last_name": "Doe",
                "date_of_birth": "1990-01-01",
                "gender": "male",
                "preferred_language": "en",
                "timezone": "America/New_York",
                "customer_segment": "premium",
                "risk_profile": "not_assessed",
                "kyc_status": "not_started",
                "role": "customer",
                "status": "pending_verification",
                "employment_status": "employed",
                "employer_name": "Acme Corp",
                "job_title": "Software Engineer",
                "industry": "Technology",
                "occupation": "Engineering"
            }
        }
    }

# Properties to receive on user creation
class UserCreate(UserBase):
    """Schema for creating a new user with required fields."""
    email: EmailStr = Field(
        ...,
        description="Primary email address for the new user account"
    )
    password: str = Field(
        ...,
        min_length=12,
        max_length=100,
        description="Strong password with minimum 12 characters, including uppercase, lowercase, number and special character"
    )
    
    # Override optional fields to make them required for creation
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    date_of_birth: date = Field(..., description="Date of birth for age verification and KYC")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "email": "new.user@example.com",
                "password": "SecurePass123!",
                "first_name": "John",
                "last_name": "Doe",
                "date_of_birth": "1990-01-01",
                "phone_number": "+919876543210",
                "gender": "male"
            }
        }
    }
    
    @field_validator('password')
    @classmethod
    def password_strength(cls, v: str) -> str:
        """Validate password meets security requirements."""
        if len(v) < 12:
            raise ValueError('Password must be at least 12 characters long')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one number')
        if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in v):
            raise ValueError('Password must contain at least one special character')
        return v
    
    @field_validator('date_of_birth')
    @classmethod
    def validate_age(cls, v: date) -> date:
        """Ensure user is at least 18 years old."""
        today = date.today()
        age = today.year - v.year - ((today.month, today.day) < (v.month, v.day))
        if age < 18:
            raise ValueError('User must be at least 18 years old')
        return v

# Properties to receive on user update
class UserUpdate(BaseModel):
    """Schema for updating user profile information."""
    email: Optional[EmailStr] = Field(
        None,
        description="New email address (requires verification)"
    )
    phone_number: Optional[str] = Field(
        None,
        min_length=10,
        max_length=20,
        pattern=r'^\+?[1-9]\d{1,14}$',
        description="New phone number (requires verification)"
    )
    first_name: Optional[str] = Field(
        None,
        min_length=1,
        max_length=100,
        description="Updated first name"
    )
    middle_name: Optional[str] = Field(
        None,
        max_length=100,
        description="Updated middle name"
    )
    last_name: Optional[str] = Field(
        None,
        min_length=1,
        max_length=100,
        description="Updated last name"
    )
    preferred_language: Optional[str] = Field(
        None,
        min_length=2,
        max_length=10,
        description="Preferred language code (ISO 639-1)"
    )
    timezone: Optional[str] = Field(
        None,
        description="Preferred timezone (IANA format)"
    )
    profile_picture_url: Optional[HttpUrl] = Field(
        None,
        description="URL to updated profile picture"
    )
    signature_url: Optional[HttpUrl] = Field(
        None,
        description="URL to updated digital signature"
    )
    customer_segment: Optional[CustomerSegment] = Field(
        None,
        description="Updated customer segment"
    )
    risk_profile: Optional[RiskProfile] = Field(
        None,
        description="Updated risk profile"
    )
    employment_status: Optional[EmploymentStatus] = Field(
        None,
        description="Updated employment status"
    )
    employer_name: Optional[str] = Field(
        None,
        max_length=200,
        description="Updated employer/organization name"
    )
    job_title: Optional[str] = Field(
        None,
        max_length=200,
        description="Updated job title/position"
    )
    industry: Optional[str] = Field(
        None,
        max_length=100,
        description="Updated industry/sector"
    )
    occupation: Optional[str] = Field(
        None,
        max_length=100,
        description="Updated occupation category"
    )
    password: Optional[str] = Field(
        None,
        min_length=12,
        max_length=100,
        description="New password (requires current password)"
    )
    current_password: Optional[str] = Field(
        None,
        min_length=12,
        max_length=100,
        description="Current password for verification"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "first_name": "John",
                "last_name": "Doe",
                "phone_number": "+919876543210",
                "timezone": "America/New_York",
                "profile_picture_url": "https://example.com/profiles/john_doe.jpg",
                "employment_status": "employed",
                "employer_name": "Acme Corp",
                "job_title": "Senior Software Engineer"
            }
        }
    
    @field_validator('password')
    @classmethod
    def validate_password_change(cls, v, info):
        """Validate password change requires current_password."""
        values = info.data
        if v is not None and 'current_password' not in values:
            raise ValueError('Current password is required to change password')
        return v
    
    @field_validator('password')
    @classmethod
    def validate_password_strength(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            if len(v) < 12:
                raise ValueError('Password must be at least 12 characters long')
            if not any(c.isupper() for c in v):
                raise ValueError('Password must contain at least one uppercase letter')
            if not any(c.islower() for c in v):
                raise ValueError('Password must contain at least one lowercase letter')
            if not any(c.isdigit() for c in v):
                raise ValueError('Password must contain at least one number')
            if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in v):
                raise ValueError('Password must contain at least one special character')
        return v

# Properties shared by models stored in DB
class UserInDBBase(UserBase, IDSchemaMixin, TimestampMixin):
    """Base schema for user data stored in the database."""
    id: int = Field(..., description="Primary key")
    hashed_password: str = Field(..., description="Hashed password using Argon2")
    salt: str = Field(..., description="Cryptographic salt for password hashing")
    mfa_enabled: bool = Field(False, description="Is multi-factor authentication enabled?")
    mfa_method: Optional[MFAMethod] = Field(None, description="Primary MFA method in use")
    last_login_at: Optional[datetime] = Field(None, description="Last successful login timestamp")
    last_login_ip: Optional[str] = Field(None, description="IP address of last login")
    last_failed_login: Optional[datetime] = Field(None, description="Last failed login attempt")
    failed_login_attempts: int = Field(0, description="Count of consecutive failed login attempts")
    account_locked_until: Optional[datetime] = Field(None, description="Account lock expiration time")
    email_verified: bool = Field(False, description="Is primary email verified?")
    email_verified_at: Optional[datetime] = Field(None, description="When primary email was verified")
    phone_verified: bool = Field(False, description="Is primary phone verified?")
    phone_verified_at: Optional[datetime] = Field(None, description="When primary phone was verified")
    last_password_change: Optional[datetime] = Field(None, description="When password was last changed")
    password_expires_at: Optional[datetime] = Field(None, description="When current password expires")
    suspicious_activity_detected: bool = Field(False, description="Flag for potential security issues")
    id_verification_status: Optional[str] = Field(None, description="Overall identity verification status")
    id_verification_date: Optional[datetime] = Field(None, description="When identity was last verified")
    created_by: Optional[int] = Field(None, description="User ID of creator (for admin-created accounts)")
    updated_by: Optional[int] = Field(None, description="User ID of last updater")
    deleted_at: Optional[datetime] = Field(None, description="When user was soft-deleted")
    deleted_by: Optional[int] = Field(None, description="User ID who performed soft delete")
    version_id: int = Field(0, description="Version number for optimistic concurrency control")
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }

# Properties to return to client
class User(UserInDBBase):
    """Schema for user data returned to the client (excludes sensitive fields)."""
    # Override sensitive fields to exclude them from API responses
    hashed_password: Optional[str] = Field(None, exclude=True)
    salt: Optional[str] = Field(None, exclude=True)
    mfa_secret: Optional[str] = Field(None, exclude=True)
    backup_codes: Optional[List[str]] = Field(None, exclude=True)
    security_questions: Optional[Dict[str, Any]] = Field(None, exclude=True)
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": 1,
                "customer_number": "CUST123456",
                "email": "user@example.com",
                "first_name": "John",
                "last_name": "Doe",
                "status": "active",
                "role": "customer",
                "email_verified": True,
                "phone_verified": True,
                "created_at": "2023-01-01T00:00:00Z",
                "updated_at": "2023-01-01T00:00:00Z"
            }
        }

# Properties stored in DB
class UserInDB(UserInDBBase):
    """Schema for complete user data as stored in the database."""
    mfa_secret: Optional[str] = Field(None, description="Encrypted MFA secret for TOTP")
    backup_codes: Optional[List[str]] = Field(None, description="Encrypted backup codes for MFA recovery")
    security_questions: Optional[Dict[str, Any]] = Field(
        None,
        description="Encrypted security questions and answers"
    )
    address: Optional[Dict[str, Any]] = Field(
        None,
        description="Primary address in structured format"
    )
    addresses: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="All associated addresses (billing, shipping, etc.)"
    )
    phone_numbers: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="All associated phone numbers with types and verification status"
    )
    emails: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="All associated email addresses with verification status"
    )
    emergency_contacts: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Emergency contact information"
    )
    trusted_contacts: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Trusted contacts for verification"
    )
    social_profiles: Optional[Dict[str, Any]] = Field(
        None,
        description="Connected social media accounts"
    )
    preferences: Dict[str, Any] = Field(
        default_factory=dict,
        description="User preferences and settings"
    )
    consent_status: Dict[str, bool] = Field(
        default_factory=lambda: {
            'terms_of_service': False,
            'privacy_policy': False,
            'electronic_communications': False,
            'data_sharing': False,
            'marketing': False
        },
        description="User consent status for various policies"
    )
    
    class Config:
        from_attributes = True

# Session schemas
class SessionBase(BaseModel):
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    expires_at: datetime
    is_active: bool = True

class SessionCreate(SessionBase):
    token: str
    user_id: int

class SessionInDBBase(SessionBase, IDSchemaMixin, TimestampMixin):
    user_id: int
    
    class Config:
        from_attributes = True

class Session(SessionInDBBase):
    pass

# Token schemas
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class TokenPayload(BaseModel):
    sub: Optional[int] = None
    exp: Optional[datetime] = None
    
# Email verification
class EmailVerificationCreate(BaseModel):
    email: EmailStr

class PhoneVerificationCreate(BaseModel):
    phone_number: str

# Reset password
class ResetPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordConfirm(BaseModel):
    token: str
    new_password: str
    
    @field_validator('new_password')
    @classmethod
    def password_strength(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one number')
        return v

# Response models
class UserResponse(BaseModel):
    success: bool = True
    data: User

class UsersResponse(BaseModel):
    success: bool = True
    data: List[User]
    total: int
    page: int
    page_size: int
