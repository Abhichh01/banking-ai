"""
Account and card related Pydantic schemas with comprehensive validation and documentation.
"""
from datetime import date, datetime, timedelta
from decimal import Decimal
from enum import Enum
from typing import Optional, List, Dict, Any, Union, Literal
from pydantic import BaseModel, Field, model_validator, field_validator , validator
from calendar import monthrange

from .base import BaseSchema, TimestampMixin, IDSchemaMixin, PaginationSchema

# Enums
class AccountType(str, Enum):
    """Types of bank accounts with detailed categorization.
    
    Attributes:
        CHECKING: Standard checking account for daily transactions
        SAVINGS: Interest-bearing savings account
        CREDIT: Revolving credit line account
        LOAN: Installment loan account
        MORTGAGE: Real estate mortgage account
        INVESTMENT: Investment/brokerage account
        MONEY_MARKET: Money market account
        CD: Certificate of Deposit
        IRA: Individual Retirement Account
        ROTH_IRA: Roth IRA
        ROLLOVER_IRA: Rollover IRA
        TRADITIONAL_IRA: Traditional IRA
        SEP_IRA: SEP IRA
        SIMPLE_IRA: SIMPLE IRA
        KEOGH: Keogh plan
        401K: 401(k) retirement account
        403B: 403(b) retirement account
        457B: 457(b) retirement account
        PENSION: Pension account
        ANNUITY: Annuity account
        COMMERCIAL: Commercial banking account
        MERCHANT: Merchant services account
        PAYROLL: Payroll account
        TAX: Tax account
        FOREIGN: Foreign currency account
    """
    # Standard accounts
    CHECKING = "checking"
    SAVINGS = "savings"
    
    # Credit and loan accounts
    CREDIT = "credit"
    LOAN = "loan"
    MORTGAGE = "mortgage"
    
    # Investment and retirement accounts
    INVESTMENT = "investment"
    MONEY_MARKET = "money_market"
    CD = "certificate_of_deposit"
    
    # Retirement accounts
    IRA = "ira"
    ROTH_IRA = "roth_ira"
    ROLLOVER_IRA = "rollover_ira"
    TRADITIONAL_IRA = "traditional_ira"
    SEP_IRA = "sep_ira"
    SIMPLE_IRA = "simple_ira"
    KEOGH = "keogh"
    _401K = "401k"
    _403B = "403b"
    _457B = "457b"
    PENSION = "pension"
    ANNUITY = "annuity"
    
    # Special purpose accounts
    BUSINESS = "business"
    COMMERCIAL = "commercial"
    MERCHANT = "merchant"
    PAYROLL = "payroll"
    TAX = "tax"
    FOREIGN = "foreign"
    ESCROW = "escrow"
    TRUST = "trust"
    
    @classmethod
    def is_retirement_account(cls, account_type: Union[str, 'AccountType']) -> bool:
        """Check if the account type is a retirement account."""
        return account_type in [
            cls.IRA, cls.ROTH_IRA, cls.ROLLOVER_IRA, 
            cls.TRADITIONAL_IRA, cls.SEP_IRA, cls.SIMPLE_IRA,
            cls.KEOGH, cls._401K, cls._403B, cls._457B, cls.PENSION
        ]
    
    @classmethod
    def is_loan_account(cls, account_type: Union[str, 'AccountType']) -> bool:
        """Check if the account type is a loan account."""
        return account_type in [cls.LOAN, cls.MORTGAGE, cls.CREDIT]

class AccountStatus(str, Enum):
    """Account status values with detailed state management.
    
    Attributes:
        ACTIVE: Account is fully operational
        INACTIVE: Account exists but not in use
        FROZEN: Account is temporarily frozen (no debits allowed)
        CLOSED: Account has been closed
        DORMANT: Account is dormant due to inactivity
        RESTRICTED: Account has restrictions (e.g., only credits allowed)
        MATURED: Account has reached maturity (CDs, etc.)
        IN_COLLECTION: Account is in collection status
        CHARGED_OFF: Account has been charged off
        PENDING: Account is pending approval/activation
        REJECTED: Account application was rejected
        SUSPENDED: Account is suspended (admin action)
        FRAUD_HOLD: Account is under fraud investigation
        DECEASED: Account holder is deceased
    """
    ACTIVE = "active"
    INACTIVE = "inactive"
    FROZEN = "frozen"
    CLOSED = "closed"
    DORMANT = "dormant"
    RESTRICTED = "restricted"
    MATURED = "matured"
    IN_COLLECTION = "in_collection"
    CHARGED_OFF = "charged_off"
    PENDING = "pending"
    REJECTED = "rejected"
    SUSPENDED = "suspended"
    FRAUD_HOLD = "fraud_hold"
    DECEASED = "deceased"
    UNDER_REVIEW = "under_review"
    
    @classmethod
    def is_open_status(cls, status: Union[str, 'AccountStatus']) -> bool:
        """Check if the status indicates an open/active account."""
        return status in [cls.ACTIVE, cls.RESTRICTED, cls.UNDER_REVIEW]
    
    @classmethod
    def is_closed_status(cls, status: Union[str, 'AccountStatus']) -> bool:
        """Check if the status indicates a closed account."""
        return status in [cls.CLOSED, cls.CHARGED_OFF, cls.REJECTED, cls.DECEASED]
    
    @classmethod
    def is_restricted_status(cls, status: Union[str, 'AccountStatus']) -> bool:
        """Check if the status indicates restrictions on the account."""
        return status in [cls.FROZEN, cls.RESTRICTED, cls.SUSPENDED, cls.FRAUD_HOLD, cls.UNDER_REVIEW]

class CardType(str, Enum):
    """Types of payment cards with detailed categorization.
    
    Attributes:
        DEBIT: Standard debit card linked to a deposit account
        CREDIT: Revolving credit line card
        PREPAID: Prepaid card with loaded funds
        VIRTUAL: Digital-only card for online use
        BUSINESS: Business expense card
        FLEET: Fleet/gas card for business vehicles
        REWARDS: Points/cashback rewards card
        SECURED: Secured credit card with deposit
        CHARGE: Charge card (must be paid in full monthly)
        GIFT: Gift card with fixed value
        CORPORATE: Corporate card for business expenses
        PURCHASING: Purchasing card for business procurement
        TRAVEL: Travel rewards/benefits card
        STUDENT: Student credit card
        CO_BRANDED: Co-branded with retailer/partner
    """
    DEBIT = "debit"
    CREDIT = "credit"
    PREPAID = "prepaid"
    VIRTUAL = "virtual"
    BUSINESS = "business"
    FLEET = "fleet"
    REWARDS = " rewards"
    SECURED = "secured"
    CHARGE = "charge"
    GIFT = "gift"
    CORPORATE = "corporate"
    PURCHASING = "purchasing"
    TRAVEL = "travel"
    STUDENT = "student"
    CO_BRANDED = "co_branded"
    
    @classmethod
    def is_credit_card(cls, card_type: Union[str, 'CardType']) -> bool:
        """Check if the card type is a credit card."""
        return card_type in [cls.CREDIT, cls.REWARDS, cls.SECURED, 
                           cls.CHARGE, cls.CORPORATE, cls.TRAVEL, 
                           cls.STUDENT, cls.CO_BRANDED]
    
    @classmethod
    def is_debit_card(cls, card_type: Union[str, 'CardType']) -> bool:
        """Check if the card type is a debit card."""
        return card_type == cls.DEBIT
    
    @classmethod
    def is_business_card(cls, card_type: Union[str, 'CardType']) -> bool:
        """Check if the card is for business use."""
        return card_type in [cls.BUSINESS, cls.CORPORATE, cls.PURCHASING, cls.FLEET]

class CardStatus(str, Enum):
    """Card status values with detailed state management.
    
    Attributes:
        ACTIVE: Card is active and can be used
        INACTIVE: Card is inactive but can be reactivated
        LOST: Card has been reported lost
        STOLEN: Card has been reported stolen
        EXPIRED: Card has reached its expiration date
        BLOCKED: Card has been blocked (temporarily)
        CLOSED: Card has been permanently closed
        SUSPENDED: Card is temporarily suspended
        COMPROMISED: Card data has been compromised
        DESTROYED: Card has been destroyed
        IN_TRANSIT: Card is being shipped to cardholder
        PENDING_ACTIVATION: Card is issued but not yet activated
    """
    ACTIVE = "active"
    INACTIVE = "inactive"
    LOST = "lost"
    STOLEN = "stolen"
    EXPIRED = "expired"
    BLOCKED = "blocked"
    CLOSED = "closed"
    SUSPENDED = "suspended"
    COMPROMISED = "compromised"
    DESTROYED = "destroyed"
    IN_TRANSIT = "in_transit"
    PENDING_ACTIVATION = "pending_activation"
    REPORTED = "reported"  # For backward compatibility
    
    @classmethod
    def is_active_status(cls, status: Union[str, 'CardStatus']) -> bool:
        """Check if the status indicates the card is active."""
        return status == cls.ACTIVE
    
    @classmethod
    def is_blocked_status(cls, status: Union[str, 'CardStatus']) -> bool:
        """Check if the status indicates the card is blocked."""
        return status in [cls.BLOCKED, cls.SUSPENDED, cls.LOST, 
                         cls.STOLEN, cls.COMPROMISED, cls.REPORTED]
    
    @classmethod
    def is_permanent_status(cls, status: Union[str, 'CardStatus']) -> bool:
        """Check if the status is permanent (cannot be reactivated)."""
        return status in [cls.CLOSED, cls.DESTROYED, cls.EXPIRED]

# Shared properties
class AccountBase(BaseModel):
    """Base schema for account properties shared across schemas."""
    account_type: AccountType = Field(
        ...,
        description="Type of the account (checking, savings, loan, etc.)"
    )
    display_name: Optional[str] = Field(
        None,
        min_length=1,
        max_length=100,
        description="User-friendly display name for the account"
    )
    currency: str = Field(..., ge=0, description="Currency code (e.g., USD, INR)")

    @model_validator(mode="after")
    def validate_limits(cls, self):
        """Validate that limits are within allowed ranges."""
        current_daily = getattr(self, 'current_daily_limit', None)
        current_tx = getattr(self, 'current_transaction_limit', None)
        current_atm = getattr(self, 'current_atm_limit', None)
        daily_limit = getattr(self, 'daily_limit', None)
        if daily_limit is not None and current_daily and daily_limit > current_daily * 2:
            raise ValueError('Daily limit increase exceeds allowed threshold')
        transaction_limit = getattr(self, 'transaction_limit', None)
        if transaction_limit is not None and daily_limit is not None and transaction_limit > daily_limit:
            raise ValueError('Transaction limit cannot exceed daily limit')
        atm_limit = getattr(self, 'atm_daily_limit', None)
        if atm_limit is not None and atm_limit > 5000:
            raise ValueError('ATM daily limit exceeds allowed maximum')
        return self

    min_balance: Decimal = Field(
        Decimal('0.00'),
        ge=0,
        description="Minimum required balance to avoid fees"
    )

    overdraft_limit: Decimal = Field(
        Decimal('0.00'),
        ge=0,
        description="Maximum allowed overdraft amount"
    )
    interest_rate: Optional[Decimal] = Field(
        None,
        ge=0,
        description="Interest rate for the account"
    )
    daily_transfer_limit: Optional[Decimal] = Field(
        None,
        ge=0,
        description="Maximum daily transfer amount"
    )
    withdrawal_limit: Optional[Decimal] = Field(
        None,
        ge=0,
        description="Maximum daily withdrawal amount"
    )
    deposit_limit: Optional[Decimal] = Field(
        None,
        ge=0,
        description="Maximum daily deposit amount"
    )
    maturity_date: Optional[date] = Field(
        None,
        description="Maturity date for time-based accounts (CDs, etc.)"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Flexible field for additional account metadata"
    )
    
    @validator('maturity_date')
    def validate_maturity_date(cls, v, values):
        if v is not None and 'opened_date' in values and values['opened_date']:
            if v < values['opened_date'].date():
                raise ValueError('Maturity date must be after account opening date')
        return v
    
    @validator('withdrawal_limit', 'deposit_limit', 'daily_transfer_limit')
    def validate_specific_limits(cls, v, values, **kwargs):
        field_name = kwargs['field'].name
        
        # If the field is None, no validation needed
        if v is None:
            return v
            
        # Get account type from values or raise error if not set
        account_type = values.get('account_type')
        if account_type is None:
            raise ValueError('Account type must be set to validate limits')
            
        # Define default limits based on account type
        default_limits = {
            'CHECKING': Decimal('10000.00'),
            'SAVINGS': Decimal('5000.00'),
            'CREDIT': Decimal('0.00'),  # No withdrawal/deposit for credit cards
            'LOAN': Decimal('0.00'),    # No withdrawal/deposit for loans
            'INVESTMENT': Decimal('25000.00'),
            'BUSINESS': Decimal('50000.00'),
        }
        
        # Get the default limit for this account type, or use a high default
        default_limit = default_limits.get(account_type, Decimal('100000.00'))
        
        # Special handling for credit/loan accounts
        if account_type in ['CREDIT', 'LOAN'] and v > 0:
            raise ValueError(f'Cannot set {field_name} for {account_type} accounts')
            
        # Check if the value exceeds 10x the default limit
        if v > (default_limit * 10):
            raise ValueError(f'{field_name} cannot exceed {default_limit * 10} for {account_type} accounts')
            
        return v

# Properties to receive on account creation
class AccountCreate(AccountBase):
    """Schema for creating a new bank account."""
    user_id: int = Field(
        ...,
        description="ID of the primary account holder"
    )
    branch_id: int = Field(
        ...,
        description="ID of the branch where the account is being opened"
    )
    initial_deposit: Decimal = Field(
        0,
        ge=0,
        description="Initial deposit amount (must be >= 0)"
    )
    joint_owners: Optional[List[int]] = Field(
        None,
        description="List of user IDs for joint account holders (if any)"
    )
    
    @model_validator(mode='before')
    def validate_initial_deposit(cls, values):
        """Validate initial deposit based on account type."""
        initial_deposit = values.get('initial_deposit', 0)
        account_type = values.get('account_type')
        min_balance = values.get('min_balance', 0)
        
        # Check minimum initial deposit requirements
        if account_type == AccountType.CHECKING and initial_deposit < 25:
            raise ValueError('Minimum initial deposit for checking accounts is $25')
        elif account_type == AccountType.SAVINGS and initial_deposit < 50:
            raise ValueError('Minimum initial deposit for savings accounts is $50')
        elif account_type == AccountType.CD and initial_deposit < 1000:
            raise ValueError('Minimum initial deposit for CDs is $1000')
            
        # Ensure initial deposit meets minimum balance requirement
        if initial_deposit < min_balance:
            raise ValueError(f'Initial deposit must be at least {min_balance} to meet minimum balance requirement')
            
        return values
    
    @model_validator(mode='before')
    def set_default_limits(cls, values):
        """Set default limits based on account type if not provided."""
        account_type = values.get('account_type')
        
        # Only set defaults if the values weren't explicitly provided
        if 'withdrawal_limit' not in values:
            if account_type == AccountType.CHECKING:
                values['withdrawal_limit'] = Decimal('1000.00')
            elif account_type == AccountType.SAVINGS:
                values['withdrawal_limit'] = Decimal('500.00')
                
        if 'deposit_limit' not in values:
            values['deposit_limit'] = Decimal('10000.00')
            
        if 'daily_transfer_limit' not in values:
            if account_type == AccountType.CHECKING:
                values['daily_transfer_limit'] = Decimal('5000.00')
            elif account_type == AccountType.SAVINGS:
                values['daily_transfer_limit'] = Decimal('2500.00')
                
        return values
    
    class Config:
        schema_extra = {
            "example": {
                "account_type": "savings",
                "display_name": "My Savings Account",
                "currency": "USD",
                "initial_deposit": 100.00,
                "user_id": 1,
                "branch_id": 1,
                "is_overdraft_protected": True,
                "min_balance": 25.00,
                "interest_rate": 0.05,
                "withdrawal_limit": 500.00,
                "deposit_limit": 10000.00,
                "daily_transfer_limit": 2500.00,
                "joint_owners": [2, 3],
                "metadata": {
                    "account_purpose": "Emergency fund",
                    "tax_status": "taxable"
                }
            }
        }

# Properties to receive on account update
class AccountUpdate(BaseModel):
    """Schema for updating an existing bank account."""
    display_name: Optional[str] = Field(
        None,
        min_length=1,
        max_length=100,
        description="Updated display name for the account"
    )
    status: Optional[AccountStatus] = Field(
        None,
        description="New status for the account"
    )
    is_primary: Optional[bool] = Field(
        None,
        description="Whether to set this as the primary account"
    )
    is_overdraft_protected: Optional[bool] = Field(
        None,
        description="Whether to enable/disable overdraft protection"
    )
    min_balance: Optional[Decimal] = Field(
        None,
        ge=0,
        description="New minimum balance requirement"
    )
    overdraft_limit: Optional[Decimal] = Field(
        None,
        ge=0,
        description="New overdraft limit"
    )
    interest_rate: Optional[Decimal] = Field(
        None,
        ge=0,
        le=100,
        description="New annual interest rate (APY) as a decimal"
    )
    daily_transfer_limit: Optional[Decimal] = Field(
        None,
        ge=0,
        description="New daily transfer limit"
    )
    withdrawal_limit: Optional[Decimal] = Field(
        None,
        ge=0,
        description="New daily withdrawal limit"
    )
    deposit_limit: Optional[Decimal] = Field(
        None,
        ge=0,
        description="New daily deposit limit"
    )
    maturity_date: Optional[date] = Field(
        None,
        description="New maturity date for time-based accounts"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        None,
        description="Metadata to update (shallow merge with existing metadata)"
    )
    
    @model_validator(mode='before')
    def validate_status_change(cls, values):
        """Validate status changes (e.g., can't close an account with a balance)."""
        if 'status' in values:
            new_status = values['status']

            # Check if we're trying to close the account
            if new_status in [AccountStatus.CLOSED, AccountStatus.CHARGED_OFF]:
                current_balance = values.get('current_balance')
                if current_balance and current_balance != 0:
                    raise ValueError('Cannot close account with non-zero balance')

            # Check if we're trying to reopen a closed account
            current_status = values.get('current_status')
            if current_status in [AccountStatus.CLOSED, AccountStatus.CHARGED_OFF, AccountStatus.DECEASED]:
                if new_status not in [AccountStatus.CLOSED, AccountStatus.CHARGED_OFF, AccountStatus.DECEASED]:
                    raise ValueError('Cannot reopen a closed, charged off, or deceased account')

        return values
    
    class Config:
        schema_extra = {
            "example": {
                "display_name": "Updated Savings Account",
                "is_primary": True,
                "overdraft_limit": 1000.00,
                "interest_rate": 0.06,
                "withdrawal_limit": 1000.00,
                "metadata": {
                    "account_purpose": "Emergency fund and vacation savings"
                }
            }
        }

# Properties shared by models stored in DB
class AccountInDBBase(AccountBase, IDSchemaMixin, TimestampMixin):
    """Base schema for account data stored in the database."""
    id: int = Field(..., description="Primary key")
    account_number: str = Field(
        ...,
        min_length=8,
        max_length=34,  # IBAN max length
        description="Account number (may be masked in some contexts)",
        example="1234567890"
    )
    current_balance: Decimal = Field(
        Decimal('0.00'),
        ge=0,
        description="Current ledger balance including all posted transactions"
    )
    available_balance: Decimal = Field(
        Decimal('0.00'),
        ge=0,
        description="Available balance including overdraft, minus holds"
    )
    hold_balance: Decimal = Field(
        Decimal('0.00'),
        ge=0,
        description="Amount of funds on hold (authorized but not posted)"
    )
    user_id: int = Field(..., description="Primary account holder's user ID")
    branch_id: int = Field(..., description="ID of the branch where the account was opened")
    opened_date: datetime = Field(..., description="When the account was opened")
    last_activity: Optional[datetime] = Field(
        None,
        description="Timestamp of the last activity on this account"
    )
    last_interest_calculation: Optional[datetime] = Field(
        None,
        description="When interest was last calculated and applied"
    )
    closed_date: Optional[datetime] = Field(
        None,
        description="When the account was closed (if applicable)"
    )
    version_id: int = Field(
        1,
        description="Version number for optimistic concurrency control"
    )
    
    class Config:
        orm_mode = True
        json_encoders = {
            Decimal: lambda v: str(v.quantize(Decimal('0.01'))),
            datetime: lambda v: v.isoformat() if v else None
        }
    
    @validator('account_number')
    def validate_account_number(cls, v):
        """Basic account number validation."""
        if not v.isalnum():
            raise ValueError('Account number must contain only alphanumeric characters')
        return v
    
    @model_validator(mode="after")
    def validate_balances(cls, self):
        """Validate that balances are consistent."""
        current = getattr(self, 'current_balance', Decimal('0.00'))
        available = getattr(self, 'available_balance', Decimal('0.00'))
        hold = getattr(self, 'hold_balance', Decimal('0.00'))
        overdraft = getattr(self, 'overdraft_limit', Decimal('0.00'))

        if available > (current + overdraft):
            raise ValueError('Available balance cannot exceed current balance + overdraft limit')

        if (current - hold) < 0:
            raise ValueError('Hold amount cannot exceed current balance')

        return self

# Properties to return to client
class Account(AccountInDBBase):
    """Schema for account data returned to the client (excludes sensitive fields)."""
    masked_account_number: str = Field(
        ...,
        description="Partially masked account number for display"
    )
    days_since_last_activity: Optional[int] = Field(
        None,
        description="Number of days since last account activity"
    )
    days_until_maturity: Optional[int] = Field(
        None,
        description="Number of days until account maturity (for time-based accounts)"
    )
    
    @validator('masked_account_number', pre=True)
    def mask_account_number(cls, v, values):
        """Mask all but last 4 digits of the account number."""
        if not v and 'account_number' in values and values['account_number']:
            acct_num = values['account_number']
            return f"****{acct_num[-4:]}" if len(acct_num) > 4 else "****"
        return v or "****"
    
    @validator('days_since_last_activity', pre=True)
    def calculate_days_since_activity(cls, v, values):
        """Calculate days since last activity."""
        if v is not None:
            return v
            
        last_activity = values.get('last_activity')
        if not last_activity:
            return None
            
        if isinstance(last_activity, str):
            last_activity = datetime.fromisoformat(last_activity.replace('Z', '+00:00'))
            
        delta = datetime.utcnow() - last_activity
        return delta.days
    
    @validator('days_until_maturity', pre=True)
    def calculate_days_until_maturity(cls, v, values):
        """Calculate days until maturity for time-based accounts."""
        if v is not None:
            return v
            
        maturity_date = values.get('maturity_date')
        if not maturity_date:
            return None
            
        if isinstance(maturity_date, str):
            maturity_date = datetime.fromisoformat(maturity_date.replace('Z', '+00:00')).date()
            
        delta = maturity_date - datetime.utcnow().date()
        return delta.days if delta.days > 0 else 0
    
    class Config(AccountInDBBase.Config):
        schema_extra = {
            "example": {
                "id": 1,
                "account_number": "1234567890",
                "masked_account_number": "****7890",
                "account_type": "savings",
                "display_name": "My Savings Account",
                "currency": "USD",
                "current_balance": 5000.00,
                "available_balance": 4900.00,
                "hold_balance": 100.00,
                "min_balance": 100.00,
                "overdraft_limit": 1000.00,
                "interest_rate": 0.05,
                "status": "active",
                "is_primary": True,
                "is_joint": False,
                "is_overdraft_protected": True,
                "opened_date": "2023-01-15T10:30:00Z",
                "last_activity": "2023-06-01T14:22:10Z",
                "days_since_last_activity": 15,
                "version_id": 5,
                "created_at": "2023-01-15T10:30:00Z",
                "updated_at": "2023-06-15T09:15:22Z"
            }
        }

# Properties stored in DB
class AccountInDB(AccountInDBBase):
    """Schema for complete account data as stored in the database."""
    # Include sensitive fields that shouldn't be exposed via the API
    account_number: str = Field(..., description="Full unmasked account number")
    
    # Additional metadata fields
    created_by: Optional[int] = Field(
        None,
        description="User ID who created this account (for admin-created accounts)"
    )
    updated_by: Optional[int] = Field(
        None,
        description="User ID who last updated this account"
    )
    closed_by: Optional[int] = Field(
        None,
        description="User ID who closed this account (if applicable)"
    )
    close_reason: Optional[str] = Field(
        None,
        max_length=255,
        description="Reason for account closure"
    )
    
    class Config(AccountInDBBase.Config):
        pass

# Card schemas
class CardBase(BaseModel):
    """Base schema for card properties shared across schemas."""
    card_holder_name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Cardholder name as printed on the card"
    )
    expiry_month: int = Field(
        ...,
        ge=1,
        le=12,
        description="Expiration month (1-12)"
    )
    expiry_year: int = Field(
        ...,
        ge=datetime.now().year,
        le=datetime.now().year + 10,  # Max 10 years in future
        description="Expiration year (4 digits)"
    )
    card_type: CardType = Field(
        ...,
        description="Type of payment card"
    )
    status: CardStatus = Field(
        CardStatus.PENDING_ACTIVATION,
        description="Current status of the card"
    )
    is_contactless: bool = Field(
        True,
        description="Whether the card supports contactless payments"
    )
    is_virtual: bool = Field(
        False,
        description="Whether this is a virtual/digital-only card"
    )
    is_primary: bool = Field(
        False,
        description="Whether this is the primary card for the account"
    )
    daily_limit: Optional[Decimal] = Field(
        None,
        ge=0,
        description="Maximum daily spending limit"
    )
    transaction_limit: Optional[Decimal] = Field(
        None,
        ge=0,
        description="Maximum amount per transaction"
    )
    atm_daily_limit: Optional[Decimal] = Field(
        None,
        ge=0,
        description="Maximum daily ATM withdrawal limit"
    )
    international_enabled: bool = Field(
        False,
        description="Whether international transactions are enabled"
    )
    online_payments_enabled: bool = Field(
        True,
        description="Whether online/CNP (Card Not Present) transactions are allowed"
    )
    categories_blocked: List[str] = Field(
        default_factory=list,
        description="Merchant category codes (MCC) that are blocked for this card"
    )
    
    @validator('expiry_year')
    def validate_expiry_year(cls, v, values):
        """Validate card expiration date is in the future."""
        current_year = datetime.now().year
        current_month = datetime.now().month
        
        if 'expiry_month' in values:
            if v < current_year or (v == current_year and values['expiry_month'] < current_month):
                raise ValueError('Card has already expired')
                
        # Validate not too far in the future (industry standard is typically 5-7 years)
        if v > current_year + 10:
            raise ValueError('Expiration year is too far in the future')
            
        return v
    
    @validator('card_holder_name')
    def validate_card_holder_name(cls, v):
        """Basic validation for cardholder name."""
        # Remove extra spaces and ensure proper formatting
        name = ' '.join(v.strip().split())
        if not name.replace(' ', '').isalpha():
            raise ValueError('Cardholder name should contain only letters and spaces')
        return name.upper()  # Standardize to uppercase

class CardCreate(CardBase):
    """Schema for creating a new payment card."""
    account_id: int = Field(
        ...,
        description="ID of the account this card is linked to"
    )
    pin: str = Field(
        ...,
        min_length=4,
        max_length=6,
        pattern=r'^\d{4,6}$',
        description="PIN code (4-6 digits)"
    )
    cvv: Optional[str] = Field(
        None,
        min_length=3,
        max_length=4,
        pattern=r'^\d{3,4}$',
        description="CVV code (3-4 digits)"
    )
    currency: str = Field(..., ge=0, description="Currency code (e.g., USD, INR)")
    daily_limit: Optional[Decimal] = Field(
        None,
        ge=0,
        description="New daily spending limit"
    )
    transaction_limit: Optional[Decimal] = Field(
        None,
        ge=0,
        description="New maximum amount per transaction"
    )
    atm_daily_limit: Optional[Decimal] = Field(
        None,
        ge=0,
        description="New daily ATM withdrawal limit"
    )
    international_enabled: Optional[bool] = Field(
        None,
        description="Enable/disable international transactions"
    )
    online_payments_enabled: Optional[bool] = Field(
        None,
        description="Enable/disable online/CNP transactions"
    )
    categories_blocked: Optional[List[str]] = Field(
        None,
        description="Update list of blocked merchant category codes (MCC)"
    )
    pin: Optional[str] = Field(
        None,
        min_length=4,
        max_length=6,
        pattern=r'^\d{4,6}$',
        description="New PIN code (4-6 digits)"
    )
    cvv: Optional[str] = Field(
        None,
        min_length=3,
        max_length=4,
        pattern=r'^\d{3,4}$',
        description="Card verification value (3-4 digits)"
    )
    
    delivery_address: Optional[Dict[str, Any]] = Field(
        None,
        description="Shipping address for physical cards"
    )
    
    @validator('pin')
    def validate_pin(cls, v):
        """Validate PIN meets security requirements."""
        # Check for sequential numbers
        if v in [str(i).zfill(len(v)) for i in range(10)]:
            raise ValueError('PIN cannot be sequential numbers')
            
        # Check for repeated numbers
        if len(set(v)) == 1:
            raise ValueError('PIN cannot have all identical digits')
            
        # Check for common PINs (basic check)
        common_pins = {'1234', '0000', '1111', '1212', '1004'}
        if v in common_pins:
            raise ValueError('This PIN is too common and not allowed')
            
        return v
    
    @model_validator(mode='after')
    def set_default_limits(cls, values):
        """Set default limits based on card type if not provided."""
        card_type = values.card_type
        
        if not hasattr(values, 'daily_limit') or values.daily_limit is None:
            if card_type == CardType.DEBIT:
                values.daily_limit = Decimal('5000.00')
            elif card_type == CardType.CREDIT:
                values['daily_limit'] = Decimal('10000.00')
            elif card_type == CardType.BUSINESS:
                values['daily_limit'] = Decimal('20000.00')
                
        if 'transaction_limit' not in values:
            values['transaction_limit'] = values.get('daily_limit', Decimal('5000.00')) * Decimal('0.5')
            
        if 'atm_daily_limit' not in values:
            values['atm_daily_limit'] = Decimal('1000.00')
            
        return values
    
    class Config:
        schema_extra = {
            "example": {
                "card_holder_name": "JOHN DOE",
                "expiry_month": 12,
                "expiry_year": 2028,
                "card_type": "debit",
                "account_id": 1,
                "pin": "1234",
                "cvv": "123",
                "is_contactless": True,
                "is_virtual": False,
                "daily_limit": 5000.00,
                "transaction_limit": 2500.00,
                "atm_daily_limit": 1000.00,
                "international_enabled": False,
                "online_payments_enabled": True,
                "categories_blocked": ["7995", "7800"],  # Gambling, Government services
                "delivery_address": {
                    "line1": "123 Main St",
                    "city": "New York",
                    "state": "NY",
                    "postal_code": "10001",
                    "country": "US"
                }
            }
        }

class CardUpdate(BaseModel):
    """Schema for updating card properties."""
    status: Optional[CardStatus] = Field(
        None,
        description="New status for the card"
    )
    is_contactless: Optional[bool] = Field(
        None,
        description="Enable/disable contactless payments"
    )
    is_primary: Optional[bool] = Field(
        None,
        description="Set as primary card for the account"
    )
    daily_limit: Optional[Decimal] = Field(
        None,
        ge=0,
        description="New daily spending limit"
    )
    transaction_limit: Optional[Decimal] = Field(
        None,
        ge=0,
        description="New maximum amount per transaction"
    )
    atm_daily_limit: Optional[Decimal] = Field(
        None,
        ge=0,
        description="New daily ATM withdrawal limit"
    )
    international_enabled: Optional[bool] = Field(
        None,
        description="Enable/disable international transactions"
    )
    online_payments_enabled: Optional[bool] = Field(
        None,
        description="Enable/disable online/CNP transactions"
    )
    categories_blocked: Optional[List[str]] = Field(
        None,
        description="Update list of blocked merchant category codes (MCC)"
    )
    pin: Optional[str] = Field(
        None,
        min_length=4,
        max_length=6,
        pattern=r'^\d{4,6}$',
        description="New PIN code (4-6 digits)"
    )
    
    @model_validator(mode="after")
    def validate_limits(cls, self):
        """Validate that limits are within allowed ranges."""
        current_daily = getattr(self, 'current_daily_limit', None)
        current_tx = getattr(self, 'current_transaction_limit', None)
        current_atm = getattr(self, 'current_atm_limit', None)
        daily_limit = getattr(self, 'daily_limit', None)
        if daily_limit is not None and current_daily and daily_limit > current_daily * 2:
            raise ValueError('Daily limit increase exceeds allowed threshold')
        transaction_limit = getattr(self, 'transaction_limit', None)
        if transaction_limit is not None and daily_limit is not None and transaction_limit > daily_limit:
            raise ValueError('Transaction limit cannot exceed daily limit')
        atm_limit = getattr(self, 'atm_daily_limit', None)
        if atm_limit is not None and atm_limit > 5000:
            raise ValueError('ATM daily limit cannot exceed $5,000')
        return self
    
    class Config:
        schema_extra = {
            "example": {
                "status": "active",
                "daily_limit": 7500.00,
                "transaction_limit": 3000.00,
                "international_enabled": True,
                "categories_blocked": ["7995"]
            }
        }

class CardInDBBase(CardBase, IDSchemaMixin, TimestampMixin):
    """Base schema for card data stored in the database."""
    id: int = Field(..., description="Primary key")
    card_number: str = Field(
        ...,
        min_length=13,
        max_length=19,  # Standard card number lengths
        description="Full card number (should be encrypted in storage)"
    )
    account_id: int = Field(..., description="ID of the linked account")
    user_id: int = Field(..., description="ID of the cardholder")
    issued_date: datetime = Field(..., description="When the card was issued")
    activation_date: Optional[datetime] = Field(
        None,
        description="When the card was activated"
    )
    @model_validator(mode="after")
    def set_default_limits(cls, self):
        """Set default limits based on card type if not provided."""
        card_type = getattr(self, 'card_type', None)
        if getattr(self, 'daily_limit', None) is None:
            if card_type == CardType.DEBIT:
                self.daily_limit = Decimal('5000.00')
            elif card_type == CardType.CREDIT:
                self.daily_limit = Decimal('10000.00')
            elif card_type == CardType.BUSINESS:
                self.daily_limit = Decimal('20000.00')
        if getattr(self, 'transaction_limit', None) is None:
            self.transaction_limit = getattr(self, 'daily_limit', Decimal('5000.00')) * Decimal('0.5')
        if getattr(self, 'atm_daily_limit', None) is None:
            self.atm_daily_limit = Decimal('1000.00')
        return self
    replacement_for: Optional[int] = Field(
        None,
        description="ID of the card this one replaces (if any)"
    )
    reason_for_replacement: Optional[str] = Field(
        None,
        max_length=50,
        description="Reason for card replacement (lost, stolen, damaged, etc.)"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional card metadata"
    )
    version_id: int = Field(
        1,
        description="Version number for optimistic concurrency control"
    )
    
    class Config:
        orm_mode = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None,
            date: lambda v: v.isoformat() if v else None
        }
    
    @validator('card_number')
    def validate_card_number(cls, v):
        """Basic Luhn check for card number validity."""
        def luhn_checksum(card_number):
            def digits_of(n):
                return [int(d) for d in str(n)]
            digits = digits_of(card_number)
            odd_digits = digits[-1::-2]
            even_digits = digits[-2::-2]
            checksum = sum(odd_digits)
            for d in even_digits:
                checksum += sum(digits_of(d * 2))
            return checksum % 10
        
        # Remove any non-digit characters
        card_num = ''.join(c for c in v if c.isdigit())
        
        # Check length and Luhn algorithm
        if not (13 <= len(card_num) <= 19) or luhn_checksum(card_num) != 0:
            raise ValueError('Invalid card number')
            
        return card_num
    
    @model_validator(mode="after")
    def set_expiry_date(cls, self):
        """Set expiry_date from expiry_month and expiry_year if not set."""
        if getattr(self, 'expiry_date', None) is None and getattr(self, 'expiry_month', None) is not None and getattr(self, 'expiry_year', None) is not None:
            self.expiry_date = date(
                year=self.expiry_year,
                month=self.expiry_month,
                day=1
            ).replace(day=monthrange(self.expiry_year, self.expiry_month)[1])
        return self

class Card(CardInDBBase):
    """Schema for card data returned to the client (excludes sensitive fields)."""
    masked_number: str = Field(
        ...,
        description="Partially masked card number for display"
    )
    formatted_expiry: str = Field(
        ...,
        description="Formatted expiration date (MM/YY)"
    )
    days_until_expiry: Optional[int] = Field(
        None,
        description="Number of days until card expiration"
    )
    account_last_four: Optional[str] = Field(
        None,
        description="Last 4 digits of the linked account number"
    )
    
    @validator('masked_number', pre=True)
    def mask_card_number(cls, v, values):
        """Mask all but last 4 digits of the card number."""
        if not v and 'card_number' in values and values['card_number']:
            card_num = values['card_number']
            if len(card_num) > 4:
                # Preserve first 6 (BIN) and last 4 digits, mask the rest
                return f"{card_num[:6]}{'*' * (len(card_num) - 10)}{card_num[-4:]}"
            return f"****{card_num[-4:]}" if len(card_num) > 4 else "****"
        return v or "**** **** **** ****"
    
    @validator('formatted_expiry', pre=True)
    def format_expiry_date(cls, v, values):
        """Format expiration date as MM/YY."""
        if not v and 'expiry_date' in values and values['expiry_date']:
            expiry = values['expiry_date']
            if isinstance(expiry, str):
                expiry = date.fromisoformat(expiry)
            return expiry.strftime('%m/%y')
        return v or "**/**"
    
    @validator('days_until_expiry', pre=True)
    def calculate_days_until_expiry(cls, v, values):
        """Calculate days until card expiration."""
        if v is not None:
            return v
            
        expiry_date = values.get('expiry_date')
        if not expiry_date:
            return None
            
        if isinstance(expiry_date, str):
            expiry_date = date.fromisoformat(expiry_date)
            
        delta = expiry_date - datetime.utcnow().date()
        return delta.days if delta.days > 0 else 0
    
    class Config(CardInDBBase.Config):
        schema_extra = {
            "example": {
                "id": 1,
                "masked_number": "411111******1111",
                "card_holder_name": "JOHN DOE",
                "formatted_expiry": "12/28",
                "card_type": "debit",
                "status": "active",
                "is_contactless": True,
                "is_virtual": False,
                "is_primary": True,
                "daily_limit": 5000.00,
                "transaction_limit": 2500.00,
                "atm_daily_limit": 1000.00,
                "issued_date": "2023-01-15T10:30:00Z",
                "expiry_date": "2028-12-31",
                "days_until_expiry": 1250,
                "international_enabled": False,
                "online_payments_enabled": True,
                "created_at": "2023-01-15T10:30:00Z",
                "updated_at": "2023-06-15T09:15:22Z"
            }
        }

class CardInDB(CardInDBBase):
    """Schema for complete card data as stored in the database."""
    # Include sensitive fields that shouldn't be exposed via the API
    card_number: str = Field(..., description="Full card number (encrypted in storage)")
    pin_hash: Optional[str] = Field(
        None,
        description="Hashed PIN (never stored in plaintext)"
    )
    cvv_hash: Optional[str] = Field(
        None,
        description="Hashed CVV (never stored in plaintext or returned via API)"
    )
    
    # Additional metadata fields
    created_by: Optional[int] = Field(
        None,
        description="User ID who requested this card"
    )
    activated_by: Optional[int] = Field(
        None,
        description="User ID who activated this card"
    )
    deactivated_by: Optional[int] = Field(
        None,
        description="User ID who deactivated this card (if applicable)"
    )
    deactivation_reason: Optional[str] = Field(
        None,
        max_length=255,
        description="Reason for card deactivation"
    )
    
    class Config(CardInDBBase.Config):
        # Exclude sensitive fields from serialization
        fields = {
            'card_number': {'exclude': True},
            'pin_hash': {'exclude': True},
            'cvv_hash': {'exclude': True}
        }

# Response models
class AccountResponse(BaseModel):
    success: bool = True
    data: Account

class AccountListResponse(BaseModel):
    success: bool = True
    data: List[Account]
    total: int
    page: int
    page_size: int

class CardResponse(BaseModel):
    success: bool = True
    data: Card

class CardListResponse(BaseModel):
    success: bool = True
    data: List[Card]
    total: int
    page: int
    page_size: int

# Query parameters
class AccountFilter(PaginationSchema):
    account_type: Optional[AccountType] = None
    status: Optional[AccountStatus] = None
    currency: Optional[str] = None
    is_primary: Optional[bool] = None
    user_id: Optional[int] = None
    branch_id: Optional[int] = None
    min_balance: Optional[Decimal] = None
    max_balance: Optional[Decimal] = None

class CardFilter(PaginationSchema):
    card_type: Optional[CardType] = None
    status: Optional[CardStatus] = None
    is_virtual: Optional[bool] = None
    account_id: Optional[int] = None
    user_id: Optional[int] = None
