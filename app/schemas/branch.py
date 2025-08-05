"""
Branch and employee related Pydantic schemas.
"""
from datetime import date, time
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator, HttpUrl, conlist

from .base import BaseSchema, TimestampMixin, IDSchemaMixin, PaginationSchema

# Enums
class BranchType(str, Enum):
    MAIN = "main"
    BRANCH = "branch"
    ATM = "atm"
    KIOSK = "kiosk"
    CORPORATE = "corporate"
    PRIVATE = "private"
    FOREIGN = "foreign"

class BranchStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    TEMPORARILY_CLOSED = "temporarily_closed"
    UNDER_MAINTENANCE = "under_maintenance"

class EmployeeRole(str, Enum):
    BRANCH_MANAGER = "branch_manager"
    ASSISTANT_MANAGER = "assistant_manager"
    TELLER = "teller"
    CUSTOMER_SERVICE = "customer_service"
    OPERATIONS = "operations"
    LOAN_OFFICER = "loan_officer"
    RELATIONSHIP_MANAGER = "relationship_manager"
    SECURITY = "security"
    OTHER = "other"

# Shared properties
class BranchBase(BaseModel):
    branch_code: str = Field(..., max_length=10, pattern=r'^[A-Z0-9]{3,10}$')
    name: str = Field(..., max_length=100)
    branch_type: BranchType = BranchType.BRANCH
    status: BranchStatus = BranchStatus.ACTIVE
    phone: Optional[str] = Field(
        None, 
        max_length=20,
        pattern=r'^\+?[1-9]\d{1,14}$'  # E.164 format
    )
    email: Optional[str] = None
    address_line1: str = Field(..., max_length=255)
    address_line2: Optional[str] = Field(None, max_length=255)
    city: str = Field(..., max_length=100)
    state: str = Field(..., max_length=100)
    postal_code: Optional[str] = Field(None, max_length=20)
    country: str = "India"
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    ifsc_code: str = Field(..., max_length=20, pattern=r'^[A-Z]{4}0[A-Z0-9]{6}$')
    micr_code: Optional[str] = Field(None, max_length=20, pattern=r'^[0-9]{9}$')
    working_hours: Optional[Dict[str, List[str]]] = None  # {"monday": ["09:00-18:00"]}
    manager_name: Optional[str] = Field(None, max_length=100)
    manager_contact: Optional[str] = Field(
        None, 
        max_length=20,
        pattern=r'^\+?[1-9]\d{1,14}$'  # E.164 format
    )
    is_24x7: bool = False
    has_atm: bool = False
    has_locker: bool = False
    has_wifi: bool = False
    is_wheelchair_accessible: bool = False
    metadata: Optional[Dict[str, Any]] = None
    
    @validator('email')
    def validate_email(cls, v):
        if v and '@' not in v:
            raise ValueError('Invalid email format')
        return v

# Properties to receive on branch creation
class BranchCreate(BranchBase):
    pass

# Properties to receive on branch update
class BranchUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    status: Optional[BranchStatus] = None
    phone: Optional[str] = Field(
        None, 
        max_length=20,
        pattern=r'^\+?[1-9]\d{1,14}$'
    )
    email: Optional[str] = None
    address_line1: Optional[str] = Field(None, max_length=255)
    address_line2: Optional[str] = Field(None, max_length=255)
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=100)
    postal_code: Optional[str] = Field(None, max_length=20)
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    working_hours: Optional[Dict[str, List[str]]] = None
    manager_name: Optional[str] = Field(None, max_length=100)
    manager_contact: Optional[str] = Field(
        None, 
        max_length=20,
        pattern=r'^\+?[1-9]\d{1,14}$'
    )
    is_24x7: Optional[bool] = None
    has_atm: Optional[bool] = None
    has_locker: Optional[bool] = None
    has_wifi: Optional[bool] = None
    is_wheelchair_accessible: Optional[bool] = None
    metadata: Optional[Dict[str, Any]] = None

# Properties shared by models stored in DB
class BranchInDBBase(BranchBase, IDSchemaMixin, TimestampMixin):
    class Config:
        from_attributes = True

# Properties to return to client
class Branch(BranchInDBBase):
    full_address: str
    
    @validator('full_address', pre=True)
    def set_full_address(cls, v, values):
        if v is None:
            parts = [
                values.get('address_line1'),
                values.get('address_line2'),
                f"{values.get('city', '')}, {values.get('state', '')}",
                values.get('postal_code'),
                values.get('country')
            ]
            return ", ".join(filter(None, parts))
        return v

# Employee schemas
class EmployeeBase(BaseModel):
    employee_id: str = Field(..., max_length=20)
    first_name: str = Field(..., max_length=50)
    last_name: str = Field(..., max_length=50)
    role: EmployeeRole
    department: Optional[str] = Field(None, max_length=50)
    email: str
    phone: Optional[str] = Field(
        None, 
        max_length=20,
        pattern=r'^\+?[1-9]\d{1,14}$'  # E.164 format
    )
    join_date: date
    is_active: bool = True
    
    @validator('email')
    def validate_email(cls, v):
        if v and '@' not in v:
            raise ValueError('Invalid email format')
        return v

class EmployeeCreate(EmployeeBase):
    branch_id: int
    user_id: Optional[int] = None

class EmployeeUpdate(BaseModel):
    first_name: Optional[str] = Field(None, max_length=50)
    last_name: Optional[str] = Field(None, max_length=50)
    role: Optional[EmployeeRole] = None
    department: Optional[str] = Field(None, max_length=50)
    phone: Optional[str] = Field(
        None, 
        max_length=20,
        pattern=r'^\+?[1-9]\d{1,14}$'
    )
    is_active: Optional[bool] = None
    user_id: Optional[int] = None

class EmployeeInDBBase(EmployeeBase, IDSchemaMixin, TimestampMixin):
    branch_id: int
    user_id: Optional[int] = None
    
    class Config:
        from_attributes = True

class Employee(EmployeeInDBBase):
    full_name: str
    
    @validator('full_name', pre=True)
    def set_full_name(cls, v, values):
        if v is None and 'first_name' in values and 'last_name' in values:
            return f"{values['first_name']} {values['last_name']}"
        return v or ""

# Response models
class BranchResponse(BaseModel):
    success: bool = True
    data: Branch

class BranchListResponse(BaseModel):
    success: bool = True
    data: List[Branch]
    total: int
    page: int
    page_size: int

class EmployeeResponse(BaseModel):
    success: bool = True
    data: Employee

class EmployeeListResponse(BaseModel):
    success: bool = True
    data: List[Employee]
    total: int
    page: int
    page_size: int

# Query parameters
class BranchFilter(PaginationSchema):
    branch_type: Optional[BranchType] = None
    status: Optional[BranchStatus] = None
    city: Optional[str] = None
    state: Optional[str] = None
    has_atm: Optional[bool] = None
    has_locker: Optional[bool] = None
    is_24x7: Optional[bool] = None
    search: Optional[str] = None

class EmployeeFilter(PaginationSchema):
    branch_id: Optional[int] = None
    role: Optional[EmployeeRole] = None
    department: Optional[str] = None
    is_active: Optional[bool] = None
    search: Optional[str] = None

# Branch metrics
class BranchMetrics(BaseModel):
    branch_id: int
    total_accounts: int
    active_accounts: int
    total_balance: float
    avg_balance: float
    transactions_today: int
    transactions_this_month: int
    
    class Config:
        from_attributes = True
