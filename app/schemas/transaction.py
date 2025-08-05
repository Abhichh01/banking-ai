"""
Transaction and merchant related Pydantic schemas with comprehensive validation and documentation.

This module defines Pydantic schemas for financial transactions and merchants, including:
- Core transaction models (create, update, response)
- Merchant information models
- Enums for transaction types, statuses, and categories
- Filter and query parameter models
- Response models for API endpoints
"""
from datetime import datetime, date
from decimal import Decimal
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, field_validator, condecimal, HttpUrl, constr, validator

from .base import BaseSchema, TimestampMixin, IDSchemaMixin, PaginationSchema

# Enums
class TransactionType(str, Enum):
    """Types of financial transactions.
    
    Attributes:
        DEBIT: Debit transaction (money going out of account)
        CREDIT: Credit transaction (money coming into account)
        TRANSFER: Internal transfer between accounts
        BILL_PAYMENT: Payment towards a bill
        REFUND: Refund for a previous transaction
        REVERSAL: Transaction reversal
        FEE: Bank or service fee
        INTEREST: Interest payment or credit
        CASH_DEPOSIT: Cash deposit into account
        CASH_WITHDRAWAL: Cash withdrawal from account
        CARD_PAYMENT: Payment made via card
        UPI: UPI payment
        NEFT: NEFT transfer
        RTGS: RTGS transfer
        IMPS: IMPS transfer
    """
    DEBIT = "debit"
    CREDIT = "credit"
    TRANSFER = "transfer"
    BILL_PAYMENT = "bill_payment"
    REFUND = "refund"
    REVERSAL = "reversal"
    FEE = "fee"
    INTEREST = "interest"
    CASH_DEPOSIT = "cash_deposit"
    CASH_WITHDRAWAL = "cash_withdrawal"
    CARD_PAYMENT = "card_payment"
    UPI = "upi"
    NEFT = "neft"
    RTGS = "rtgs"
    IMPS = "imps"

class TransactionStatus(str, Enum):
    """Status of a transaction.
    
    Attributes:
        PENDING: Transaction is being processed
        COMPLETED: Transaction was successfully completed
        FAILED: Transaction failed to complete
        REVERSED: Transaction was reversed/refunded
        HOLD: Transaction is on hold for review
        CANCELLED: Transaction was cancelled
    """
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REVERSED = "reversed"
    HOLD = "hold"
    CANCELLED = "cancelled"

class TransactionCategory(str, Enum):
    SHOPPING = "shopping"
    FOOD_DINING = "food_dining"
    TRANSPORT = "transport"
    BILLS_UTILITIES = "bills_utilities"
    ENTERTAINMENT = "entertainment"
    TRAVEL = "travel"
    HEALTHCARE = "healthcare"
    EDUCATION = "education"
    TRANSFER = "transfer"
    SALARY = "salary"
    INVESTMENT = "investment"
    LOAN_EMI = "loan_emi"
    INSURANCE = "insurance"
    RENT = "rent"
    SUBSCRIPTION = "subscription"
    OTHER = "other"

class PaymentMethod(str, Enum):
    CARD = "card"
    UPI = "upi"
    NEFT = "neft"
    RTGS = "rtgs"
    IMPS = "imps"
    CASH = "cash"
    CHEQUE = "cheque"
    DD = "demand_draft"
    WALLET = "wallet"
    OTHER = "other"

# Shared properties
class TransactionBase(BaseModel):
    """Base transaction model with shared properties."""
    
    amount: Decimal = Field(
        ...,
        gt=-1_000_000_000_000,
        lt=1_000_000_000_000,
        max_digits=19,
        decimal_places=4,
        description="Transaction amount. Positive for credits, negative for debits."
    )
    currency: str = Field(
        default="INR",
        max_length=3,
        description="ISO 4217 currency code"
    )
    transaction_type: TransactionType = Field(
        ...,
        description="Type of transaction"
    )
    category: Optional[TransactionCategory] = Field(
        default=None,
        description="Category for this transaction"
    )
    description: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Human-readable description of the transaction"
    )
    reference: Optional[str] = Field(
        default=None,
        max_length=100,
        description="External reference ID for this transaction"
    )
    metadata_: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        alias="metadata",
        description="Additional metadata for the transaction"
    )
    is_recurring: bool = Field(
        default=False,
        description="Whether this is a recurring transaction"
    )
    is_international: bool = Field(
        default=False,
        description="Whether this is an international transaction"
    )
    is_flagged: bool = Field(
        default=False,
        description="Whether this transaction has been flagged for review"
    )
    fraud_score: Optional[float] = Field(
        default=None,
        ge=0,
        le=100,
        description="Fraud risk score (0-100)"
    )
    
    @validator('amount')
    def validate_amount_based_on_type(cls, v, values):
        """Validate amount based on transaction type."""
        if 'transaction_type' not in values:
            return v
            
        transaction_type = values['transaction_type']
        
        # For debit transactions, amount should be negative
        if transaction_type in [TransactionType.DEBIT, TransactionType.FEE, 
                              TransactionType.CASH_WITHDRAWAL, TransactionType.CARD_PAYMENT]:
            if v > 0:
                v = -v  # Convert to negative for debits
        # For credit transactions, amount should be positive
        elif transaction_type in [TransactionType.CREDIT, TransactionType.REFUND, 
                                TransactionType.REVERSAL, TransactionType.INTEREST,
                                TransactionType.CASH_DEPOSIT]:
            if v < 0:
                v = abs(v)  # Convert to positive for credits
                
        return v.quantize(Decimal('0.01'))  # Round to 2 decimal places
        
    @field_validator('metadata_', mode='before')
    def ensure_metadata_dict(cls, v):
        """Ensure metadata is always a dictionary."""
        return v or {}
        
    model_config = {
        "populate_by_name": True,
        "json_encoders": {
            Decimal: lambda v: str(v.quantize(Decimal('0.01')))  # Ensure consistent decimal formatting
        }
    }

# Properties to receive on transaction creation
class TransactionCreate(TransactionBase):
    """Schema for creating a new transaction."""
    
    account_id: int = Field(
        ...,
        gt=0,
        description="ID of the account this transaction belongs to"
    )
    card_id: Optional[int] = Field(
        default=None,
        gt=0,
        description="ID of the card used for this transaction, if applicable"
    )
    merchant_id: Optional[int] = Field(
        default=None,
        gt=0,
        description="ID of the merchant for this transaction, if applicable"
    )
    counterparty_name: Optional[str] = Field(
        default=None,
        max_length=255,
        description="Name of the counterparty in this transaction"
    )
    counterparty_account: Optional[str] = Field(
        default=None,
        max_length=34,
        pattern=r'^[A-Z]{2}[0-9]{2}[A-Z0-9]{1,30}$',
        description="IBAN or account number of the counterparty"
    )
    counterparty_ifsc: Optional[str] = Field(
        default=None,
        max_length=20,
        pattern=r'^[A-Za-z]{4}0[A-Z0-9]{6}$',
        description="IFSC code of the counterparty's bank"
    )
    location: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Geolocation data for the transaction"
    )
    transaction_date: Optional[datetime] = Field(
        default_factory=datetime.utcnow,
        description="Timestamp when the transaction occurred (defaults to now)"
    )
    
    @validator('location')
    def validate_location(cls, v):
        """Validate location data structure."""
        if v is None:
            return None
            
        if not isinstance(v, dict):
            raise ValueError("Location must be a dictionary")
            
        if 'latitude' in v and 'longitude' in v:
            lat = v['latitude']
            lon = v['longitude']
            if not (-90 <= lat <= 90):
                raise ValueError("Latitude must be between -90 and 90")
            if not (-180 <= lon <= 180):
                raise ValueError("Longitude must be between -180 and 180")
                
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "account_id": 1,
                "amount": -1500.50,  # Negative for debit
                "currency": "INR",
                "transaction_type": "debit",
                "category": "shopping",
                "description": "Amazon.in purchase",
                "reference": "TXN123456789",
                "counterparty_name": "Amazon Seller Services Pvt Ltd",
                "counterparty_account": "IN6802290000100529202001",
                "counterparty_ifsc": "HDFC0001234",
                "metadata": {
                    "invoice_id": "INV-12345",
                    "items": ["Item 1", "Item 2"]
                },
                "location": {
                    "latitude": 19.0760,
                    "longitude": 72.8777,
                    "address": "Amazon Development Centre, Mumbai"
                },
                "is_international": False,
                "is_recurring": False
            }
        }

# Properties to receive on transaction update
class TransactionUpdate(BaseModel):
    """Schema for updating an existing transaction."""
    
    category: Optional[TransactionCategory] = Field(
        default=None,
        description="Updated transaction category"
    )
    description: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Updated transaction description"
    )
    status: Optional[TransactionStatus] = Field(
        default=None,
        description="Updated transaction status"
    )
    is_flagged: Optional[bool] = Field(
        default=None,
        description="Flag status of the transaction"
    )
    fraud_score: Optional[float] = Field(
        default=None,
        ge=0,
        le=100,
        description="Updated fraud risk score (0-100)"
    )
    metadata_: Optional[Dict[str, Any]] = Field(
        default=None,
        alias="metadata",
        description="Additional metadata to merge with existing metadata"
    )
    
    class Config:
        validate_by_name = True
        
    @validator('metadata_', pre=True)
    def ensure_metadata_dict(cls, v):
        """Ensure metadata is always a dictionary."""
        return v or {}

# Properties shared by models stored in DB
class TransactionInDBBase(TransactionBase, IDSchemaMixin, TimestampMixin):
    """Base model for transaction data stored in the database."""
    
    reference_id: str = Field(
        ...,
        min_length=8,
        max_length=64,
        description="Unique reference ID for the transaction"
    )
    status: TransactionStatus = Field(
        default=TransactionStatus.PENDING,
        description="Current status of the transaction"
    )
    account_id: int = Field(
        ...,
        gt=0,
        description="ID of the account this transaction belongs to"
    )
    card_id: Optional[int] = Field(
        default=None,
        gt=0,
        description="ID of the card used for this transaction, if applicable"
    )
    merchant_id: Optional[int] = Field(
        default=None,
        gt=0,
        description="ID of the merchant for this transaction, if applicable"
    )
    transaction_date: datetime = Field(
        default_factory=datetime.utcnow,
        description="Timestamp when the transaction occurred"
    )
    posted_date: Optional[datetime] = Field(
        default=None,
        description="Timestamp when the transaction was posted to the account"
    )
    counterparty_name: Optional[str] = Field(
        default=None,
        max_length=255,
        description="Name of the counterparty in this transaction"
    )
    counterparty_account: Optional[str] = Field(
        default=None,
        max_length=34,
        description="IBAN or account number of the counterparty"
    )
    counterparty_ifsc: Optional[str] = Field(
        default=None,
        max_length=20,
        description="IFSC code of the counterparty's bank"
    )
    location: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Geolocation data for the transaction"
    )
    
    # Inherited fields with overridden defaults
    is_recurring: bool = Field(
        default=False,
        description="Whether this is a recurring transaction"
    )
    is_international: bool = Field(
        default=False,
        description="Whether this is an international transaction"
    )
    is_flagged: bool = Field(
        default=False,
        description="Whether this transaction has been flagged for review"
    )
    fraud_score: Optional[float] = Field(
        default=None,
        ge=0,
        le=100,
        description="Fraud risk score (0-100)"
    )
    
    class Config:
        from_attributes = True
        validate_by_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            Decimal: lambda v: str(v.quantize(Decimal('0.01')))
        }

# Properties to return to client
class Transaction(TransactionInDBBase):
    """Transaction model for API responses with computed properties."""
    
    absolute_amount: Decimal = Field(
        ...,
        description="Absolute value of the transaction amount"
    )
    is_debit: bool = Field(
        ...,
        description="Whether this is a debit transaction"
    )
    
    @validator('absolute_amount', pre=True, always=True)
    def set_absolute_amount(cls, v, values):
        """Compute absolute amount from the transaction amount."""
        if v is not None:
            return v
        if 'amount' in values:
            return abs(values['amount'])
        return Decimal('0')
    
    @validator('is_debit', pre=True, always=True)
    def set_is_debit(cls, v, values):
        """Determine if this is a debit transaction."""
        if v is not None:
            return v
        if 'amount' in values:
            return values['amount'] < 0
        return False
        
    @property
    def formatted_amount(self) -> str:
        """Return formatted amount with currency symbol."""
        if self.currency == "INR":
            return f"₹{abs(self.amount):,.2f}"
        return f"{self.currency} {abs(self.amount):,.2f}"
        
    class Config(TransactionInDBBase.Config):
        json_schema_extra = {
            "example": {
                "id": 1,
                "reference_id": "TXN123456789",
                "amount": -1500.50,
                "absolute_amount": 1500.50,
                "is_debit": True,
                "currency": "INR",
                "transaction_type": "debit",
                "category": "shopping",
                "description": "Amazon.in purchase",
                "status": "completed",
                "account_id": 1,
                "card_id": 1,
                "merchant_id": 1,
                "transaction_date": "2023-06-15T14:30:00Z",
                "posted_date": "2023-06-15T14:35:12Z",
                "counterparty_name": "Amazon Seller Services Pvt Ltd",
                "counterparty_account": "IN6802290000100529202001",
                "counterparty_ifsc": "HDFC0001234",
                "is_recurring": False,
                "is_international": False,
                "is_flagged": False,
                "fraud_score": 12.5,
                "created_at": "2023-06-15T14:35:12Z",
                "updated_at": "2023-06-15T14:35:12Z",
                "metadata": {
                    "invoice_id": "INV-12345",
                    "items": ["Item 1", "Item 2"]
                }
            }
        }

# Properties stored in DB
class TransactionInDB(TransactionInDBBase):
    """Transaction model for database storage with sensitive fields."""
    
    class Config(TransactionInDBBase.Config):
        # Include all fields by default, even if they're None
        exclude = {}
        
        # Example of how to exclude sensitive fields from logging/display
        # json_encoders = {
        #     **TransactionInDBBase.Config.json_encoders,
        #     "sensitive_field": lambda v: "***REDACTED***" if v else None
        # }

# Merchant schemas
class MerchantCategory(str, Enum):
    """Categories for classifying merchants.
    
    Attributes:
        RETAIL: General retail stores and shops
        GROCERY: Supermarkets and grocery stores
        RESTAURANT: Food and dining establishments
        TRAVEL: Travel-related services (hotels, airlines, etc.)
        TRANSPORT: Transportation services (taxis, ride-sharing, etc.)
        UTILITIES: Utility service providers
        ENTERTAINMENT: Entertainment and leisure
        HEALTHCARE: Medical and healthcare services
        EDUCATION: Educational institutions
        FINANCIAL: Financial institutions and services
        GOVERNMENT: Government agencies
        OTHER: Other categories not listed
    """
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

class MerchantBase(BaseModel):
    """Base model for merchant information."""
    
    name: str = Field(
        ...,
        max_length=255,
        description="Legal name of the merchant"
    )
    merchant_id: Optional[str] = Field(
        default=None,
        max_length=50,
        description="External merchant identifier (MID)"
    )
    category: MerchantCategory = Field(
        ...,
        description="Business category of the merchant"
    )
    website: Optional[HttpUrl] = Field(
        default=None,
        description="Official website URL of the merchant"
    )
    phone: Optional[str] = Field(
        default=None,
        max_length=20,
        pattern=r'^\+?[1-9]\d{1,14}$',  # E.164 format
        description="Contact phone number in E.164 format"
    )
    email: Optional[str] = Field(
        default=None,
        max_length=255,
        pattern=r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
        description="Business email address"
    )
    is_online: bool = Field(
        default=False,
        description="Whether this is an online merchant"
    )
    is_verified: bool = Field(
        default=False,
        description="Whether the merchant has been verified"
    )
    metadata_: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        alias="metadata",
        description="Additional merchant metadata"
    )
    
    @validator('name')
    def validate_name(cls, v):
        """Validate merchant name is not empty after stripping."""
        if not v or not v.strip():
            raise ValueError("Merchant name cannot be empty")
        return v.strip()
    
    @validator('merchant_id')
    def validate_merchant_id(cls, v):
        """Validate merchant ID format if provided."""
        if v is not None and not v.strip():
            return None
        return v
    
    class Config:
        validate_by_name = True
        json_encoders = {
            # Add any custom JSON encoders if needed
        }

class MerchantCreate(MerchantBase):
    """Schema for creating a new merchant."""
    
    address: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Physical address information"
    )
    
    @validator('address')
    def validate_address(cls, v):
        """Validate address structure if provided."""
        if v is None:
            return None
            
        if not isinstance(v, dict):
            raise ValueError("Address must be a dictionary")
            
        # Basic address validation
        required_fields = ['street', 'city', 'country', 'postal_code']
        for field in required_fields:
            if field not in v or not str(v[field]).strip():
                raise ValueError(f"Address must contain a non-empty {field} field")
                
        # Validate coordinates if present
        if 'coordinates' in v:
            coords = v['coordinates']
            if not isinstance(coords, dict) or 'latitude' not in coords or 'longitude' not in coords:
                raise ValueError("Coordinates must contain 'latitude' and 'longitude'")
                
            lat, lon = coords['latitude'], coords['longitude']
            if not (-90 <= lat <= 90):
                raise ValueError("Latitude must be between -90 and 90")
            if not (-180 <= lon <= 180):
                raise ValueError("Longitude must be between -180 and 180")
                
        return v
    
    class Config(MerchantBase.Config):
        json_schema_extra = {
            "example": {
                "name": "Acme Corp",
                "merchant_id": "ACME123456",
                "category": "retail",
                "website": "https://acme.example.com",
                "phone": "+919876543210",
                "email": "contact@acme.example.com",
                "is_online": True,
                "is_verified": True,
                "metadata": {
                    "tax_id": "TAX12345",
                    "gstin": "22AAAAA0000A1Z5"
                },
                "address": {
                    "street": "123 Business Park",
                    "city": "Mumbai",
                    "state": "Maharashtra",
                    "country": "India",
                    "postal_code": "400001",
                    "coordinates": {
                        "latitude": 19.0760,
                        "longitude": 72.8777
                    }
                }
            }
        }

class MerchantUpdate(BaseModel):
    """Schema for updating an existing merchant."""
    
    name: Optional[str] = Field(
        default=None,
        max_length=255,
        description="Updated merchant name"
    )
    category: Optional[MerchantCategory] = Field(
        default=None,
        description="Updated business category"
    )
    website: Optional[HttpUrl] = Field(
        default=None,
        description="Updated website URL"
    )
    phone: Optional[str] = Field(
        default=None,
        max_length=20,
        pattern=r'^\+?[1-9]\d{1,14}$',  # E.164 format
        description="Updated contact phone number"
    )
    email: Optional[str] = Field(
        default=None,
        max_length=255,
        pattern=r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
        description="Updated email address"
    )
    is_online: Optional[bool] = Field(
        default=None,
        description="Update online status"
    )
    is_verified: Optional[bool] = Field(
        default=None,
        description="Update verification status"
    )
    metadata_: Optional[Dict[str, Any]] = Field(
        default=None,
        alias="metadata",
        description="Metadata to merge with existing metadata"
    )
    address: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Updated address information"
    )
    
    @validator('name')
    def validate_name(cls, v):
        """Validate merchant name is not empty if provided."""
        if v is not None and not v.strip():
            raise ValueError("Merchant name cannot be empty")
        return v.strip() if v else v
    
    @validator('metadata_', pre=True)
    def ensure_metadata_dict(cls, v):
        """Ensure metadata is always a dictionary."""
        return v or {}
    
    class Config:
        validate_by_name = True

class MerchantInDBBase(MerchantBase, IDSchemaMixin, TimestampMixin):
    """Base model for merchant data stored in the database."""
    
    address: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Physical address information"
    )
    
    class Config(MerchantBase.Config):
        from_attributes = True
        json_encoders = {
            **MerchantBase.Config.json_encoders,
            # Add any additional encoders for database-specific fields
        }

class Merchant(MerchantInDBBase):
    """Merchant model for API responses with additional computed properties."""
    
    @property
    def display_name(self) -> str:
        """Return a display-friendly name for the merchant."""
        return self.name.strip()
    
    @property
    def location(self) -> Optional[Dict[str, float]]:
        """Extract location coordinates from address if available."""
        if not self.address or 'coordinates' not in self.address:
            return None
        return self.address['coordinates']
    
    class Config(MerchantInDBBase.Config):
        json_schema_extra = {
            "example": {
                "id": 1,
                "name": "Acme Corp",
                "merchant_id": "ACME123456",
                "category": "retail",
                "website": "https://acme.example.com",
                "phone": "+919876543210",
                "email": "contact@acme.example.com",
                "is_online": True,
                "is_verified": True,
                "created_at": "2023-06-15T14:30:00Z",
                "updated_at": "2023-06-15T14:30:00Z",
                "metadata": {
                    "tax_id": "TAX12345",
                    "gstin": "22AAAAA0000A1Z5"
                },
                "address": {
                    "street": "123 Business Park",
                    "city": "Mumbai",
                    "state": "Maharashtra",
                    "country": "India",
                    "postal_code": "400001",
                    "coordinates": {
                        "latitude": 19.0760,
                        "longitude": 72.8777
                    }
                }
            }
        }    

class Merchant(MerchantInDBBase):
    pass

# Response models
class TransactionResponse(BaseModel):
    success: bool = True
    data: Transaction

class TransactionListResponse(BaseModel):
    success: bool = True
    data: List[Transaction]
    total: int
    page: int
    page_size: int

class MerchantResponse(BaseModel):
    """Standard response format for single merchant operations."""
    success: bool = Field(
        default=True,
        description="Indicates if the operation was successful"
    )
    data: Merchant = Field(
        ...,
        description="The merchant data"
    )
    
    class Config:
        json_encoders = {
            **Merchant.Config.json_encoders
        }
        json_schema_extra = {
            "example": {
                "success": True,
                "data": {
                    "id": 1,
                    "name": "Acme Corp",
                    "merchant_id": "ACME123456",
                    "category": "retail",
                    "website": "https://acme.example.com",
                    "phone": "+919876543210",
                    "is_online": True,
                    "is_verified": True,
                    "created_at": "2023-06-15T14:30:00Z",
                    "updated_at": "2023-06-15T14:30:00Z"
                }
            }
        }

class MerchantListResponse(BaseModel):
    """Paginated response for merchant listings."""
    success: bool = Field(
        default=True,
        description="Indicates if the operation was successful"
    )
    data: List[Merchant] = Field(
        ...,
        description="List of merchants"
    )
    total: int = Field(
        ...,
        ge=0,
        description="Total number of merchants matching the query"
    )
    page: int = Field(
        ...,
        ge=1,
        description="Current page number (1-based)"
    )
    page_size: int = Field(
        ...,
        ge=1,
        le=100,
        description="Number of items per page"
    )
    
    class Config:
        json_encoders = {
            **Merchant.Config.json_encoders
        }
        json_schema_extra = {
            "example": {
                "success": True,
                "data": [
                    {
                        "id": 1,
                        "name": "Acme Corp",
                        "category": "retail",
                        "is_online": True,
                        "is_verified": True
                    },
                    {
                        "id": 2,
                        "name": "Global Foods",
                        "category": "grocery",
                        "is_online": True,
                        "is_verified": True
                    }
                ],
                "total": 2,
                "page": 1,
                "page_size": 10
            }
        }

# Query parameters
class TransactionFilter(PaginationSchema):
    account_id: Optional[int] = None
    card_id: Optional[int] = None
    merchant_id: Optional[int] = None
    transaction_type: Optional[TransactionType] = None
    category: Optional[TransactionCategory] = None
    status: Optional[TransactionStatus] = None
    min_amount: Optional[Decimal] = None
    max_amount: Optional[Decimal] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    reference: Optional[str] = None
    search: Optional[str] = None

class MerchantFilter(BaseModel):
    """Filter criteria for querying merchants."""
    
    category: Optional[MerchantCategory] = Field(
        default=None,
        description="Filter by merchant category"
    )
    is_online: Optional[bool] = Field(
        default=None,
        description="Filter by online status"
    )
    is_verified: Optional[bool] = Field(
        default=None,
        description="Filter by verification status"
    )
    search: Optional[str] = Field(
        default=None,
        max_length=255,
        description="Search term to filter merchants by name or ID"
    )
    min_transactions: Optional[int] = Field(
        default=None,
        ge=0,
        description="Minimum number of transactions for the merchant"
    )
    max_transactions: Optional[int] = Field(
        default=None,
        ge=0,
        description="Maximum number of transactions for the merchant"
    )
    created_after: Optional[date] = Field(
        default=None,
        description="Filter merchants created after this date"
    )
    created_before: Optional[date] = Field(
        default=None,
        description="Filter merchants created before this date"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "category": "retail",
                "is_online": True,
                "is_verified": True,
                "search": "acme",
                "min_transactions": 10,
                "created_after": "2023-01-01"
            }
        }

# Transaction summary
class TransactionSummary(BaseModel):
    total_credits: Decimal = Decimal('0')
    total_debits: Decimal = Decimal('0')
    net_amount: Decimal = Decimal('0')
    transaction_count: int = 0
    
    class Config:
        json_encoders = {Decimal: str}

# Bulk transaction import
class BulkTransactionCreate(BaseModel):
    transactions: List[TransactionCreate]
    skip_duplicates: bool = True
