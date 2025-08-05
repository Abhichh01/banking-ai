"""
Account model for managing user bank accounts with comprehensive features.

This module defines the Account and related models that handle all banking account
operations, including transactions, cards, and account management features.
"""
from __future__ import annotations

from datetime import datetime, date, timedelta
from decimal import Decimal, ROUND_HALF_UP
from enum import Enum, auto
from typing import Optional, List, Dict, Any, Union, TYPE_CHECKING
from uuid import uuid4

from sqlalchemy import (
    Column, String, Numeric, DateTime, Integer, ForeignKey, 
    Enum as SQLEnum, Boolean, Index, CheckConstraint, 
    Date, Text, func, event, DDL, Table
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship, validates, Mapped
from sqlalchemy.ext.hybrid import hybrid_property

# Import database-agnostic types
from app.db.types import JSON, UUID, Interval

from .base import ModelBase

if TYPE_CHECKING:
    from .user import User
    from .transaction import Transaction
    from .card import Card


class AccountType(str, Enum):
    """Types of bank accounts with detailed categorization.
    
    Attributes:
        CHECKING: Standard checking account for daily transactions
        SAVINGS: Interest-bearing savings account
        CREDIT: Revolving credit line account
        LOAN: Installment loan account
        MORTGAGE: Real estate mortgage account
        INVESTMENT: Investment/brokerage account
        BUSINESS: Business checking/savings account
        STUDENT: Student-specific account
        SENIOR: Senior citizen account
        JOINT: Joint ownership account
        TRUST: Trust account
        ESCROW: Escrow account
        MONEY_MARKET: Money market account
        CD: Certificate of Deposit
        HSA: Health Savings Account
        FSA: Flexible Spending Account
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
        OTHER: Other account type
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
    HSA = "hsa"
    FSA = "fsa"
    
    # Business and commercial
    BUSINESS = "business"
    COMMERCIAL = "commercial"
    MERCHANT = "merchant"
    PAYROLL = "payroll"
    TAX = "tax"
    
    # Other
    STUDENT = "student"
    SENIOR = "senior"
    JOINT = "joint"
    TRUST = "trust"
    ESCROW = "escrow"
    FOREIGN = "foreign"
    OTHER = "other"
    
    @classmethod
    def is_retirement_account(cls, account_type: Union[str, 'AccountType']) -> bool:
        """Check if an account type is a retirement account."""
        retirement_types = {
            cls.IRA, cls.ROTH_IRA, cls.ROLLOVER_IRA, cls.TRADITIONAL_IRA,
            cls.SEP_IRA, cls.SIMPLE_IRA, cls.KEOGH, cls._401K, cls._403B,
            cls._457B, cls.PENSION, cls.ANNUITY
        }
        return account_type in retirement_types
    
    @classmethod
    def is_loan_account(cls, account_type: Union[str, 'AccountType']) -> bool:
        """Check if an account type is a loan or credit account."""
        return account_type in {cls.CREDIT, cls.LOAN, cls.MORTGAGE}
    
    @classmethod
    def is_deposit_account(cls, account_type: Union[str, 'AccountType']) -> bool:
        """Check if an account type is a deposit account (checking/savings)."""
        return account_type in {cls.CHECKING, cls.SAVINGS, cls.BUSINESS, 
                              cls.STUDENT, cls.SENIOR, cls.JOINT}


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
    # Standard statuses
    ACTIVE = "active"
    INACTIVE = "inactive"
    FROZEN = "frozen"
    CLOSED = "closed"
    DORMANT = "dormant"
    
    # Additional statuses for better control
    RESTRICTED = "restricted"
    MATURED = "matured"
    IN_COLLECTION = "in_collection"
    CHARGED_OFF = "charged_off"
    PENDING = "pending"
    REJECTED = "rejected"
    SUSPENDED = "suspended"
    FRAUD_HOLD = "fraud_hold"
    DECEASED = "deceased"
    
    @classmethod
    def is_open_status(cls, status: Union[str, 'AccountStatus']) -> bool:
        """Check if the status indicates an open/active account."""
        return status in {cls.ACTIVE, cls.RESTRICTED, cls.PENDING}
    
    @classmethod
    def is_closed_status(cls, status: Union[str, 'AccountStatus']) -> bool:
        """Check if the status indicates a closed account."""
        return status in {cls.CLOSED, cls.CHARGED_OFF, cls.REJECTED, cls.DECEASED}
    
    @classmethod
    def is_restricted_status(cls, status: Union[str, 'AccountStatus']) -> bool:
        """Check if the status indicates restrictions on the account."""
        return status in {cls.FROZEN, cls.RESTRICTED, cls.SUSPENDED, 
                         cls.FRAUD_HOLD, cls.IN_COLLECTION}


class Account(ModelBase):
    """Comprehensive bank account model with advanced features and security.
    
    This model represents a financial account in the banking system, supporting
    various account types, transaction tracking, and financial operations.
    """
    
    __tablename__ = "accounts"
    
    # Primary key
    id = Column(UUID, primary_key=True, default=uuid4, index=True, unique=True, nullable=False,
               comment='Unique identifier for the account')
    
    __table_args__ = (
        # Core indexes
        Index('idx_account_user', 'user_id', 'account_type'),
        Index('idx_account_number', 'account_number', unique=True),
        
        # Database-agnostic primary account index
        Index('idx_account_primary', 'user_id', 'is_primary', 
              unique=True, 
              sqlite_where=(Column('is_primary') == 1),
              mssql_where=(Column('is_primary') == 1)),
        
        Index('idx_account_status', 'status', 'last_activity'),
        
        # Performance indexes
        Index('idx_account_balance', 'current_balance', 'available_balance'),
        Index('idx_account_dates', 'opened_date', 'last_activity', 'closed_date'),
        
        # Check constraints with database-agnostic syntax
        CheckConstraint('current_balance >= min_balance', name='check_balance_above_min'),
        CheckConstraint('available_balance >= 0', name='check_available_balance_non_negative'),
        CheckConstraint('interest_rate >= 0', name='check_interest_rate_non_negative'),
        CheckConstraint('overdraft_limit >= 0', name='check_overdraft_limit_non_negative'),
        CheckConstraint('daily_transfer_limit >= 0', name='check_daily_limit_non_negative'),
        CheckConstraint('withdrawal_limit >= 0', name='check_withdrawal_limit_non_negative'),
        CheckConstraint('deposit_limit >= 0', name='check_deposit_limit_non_negative'),
        
        # Database-agnostic date comparisons
        CheckConstraint(
            "closed_date IS NULL OR closed_date >= opened_date",
            name="check_closed_after_opened"
        ),
        CheckConstraint(
            "maturity_date IS NULL OR maturity_date >= opened_date",
            name="check_maturity_after_opened"
        ),
        CheckConstraint(
            "closed_date IS NULL OR status IN ('closed', 'charged_off', 'rejected')",
            name="check_closed_status"
        ),
        {'extend_existing': True}
    )
    
    # ===== Account Identification =====
    account_number = Column(
        String(34), 
        unique=True, 
        nullable=False, 
        index=True,
        comment="IBAN format account number for international transfers"
    )
    
    account_type = Column(
        SQLEnum(AccountType), 
        nullable=False,
        index=True,
        comment="Type of the account (checking, savings, loan, etc.)"
    )
    
    display_name = Column(
        String(100), 
        nullable=True,
        comment="User-friendly display name for the account"
    )
    
    # ===== Account Details =====
    currency = Column(
        String(3), 
        default="USD", 
        nullable=False,
        comment="ISO 4217 currency code (e.g., USD, EUR, GBP)"
    )
    
    current_balance = Column(
        Numeric(19, 4), 
        default=Decimal('0.00'), 
        nullable=False,
        comment="Current ledger balance including all posted transactions"
    )
    
    available_balance = Column(
        Numeric(19, 4), 
        default=Decimal('0.00'), 
        nullable=False,
        comment="Available balance including overdraft, minus holds"
    )
    
    hold_balance = Column(
        Numeric(19, 4),
        default=Decimal('0.00'),
        nullable=False,
        comment="Amount of funds on hold (authorized but not posted)"
    )
    
    min_balance = Column(
        Numeric(19, 4),
        default=Decimal('0.00'),
        nullable=False,
        comment="Minimum required balance to avoid fees"
    )
    
    # ===== Status and Flags =====
    status = Column(
        SQLEnum(AccountStatus), 
        default=AccountStatus.PENDING, 
        nullable=False,
        index=True,
        comment="Current status of the account"
    )
    
    is_primary = Column(
        Boolean, 
        default=False, 
        nullable=False,
        comment="Whether this is the user's primary account"
    )
    
    is_joint = Column(
        Boolean,
        default=False,
        nullable=False,
        comment="Whether this is a joint account with multiple owners"
    )
    
    is_overdraft_protected = Column(
        Boolean,
        default=False,
        nullable=False,
        comment="Whether overdraft protection is enabled"
    )
    
    # ===== Dates =====
    opened_date = Column(
        DateTime, 
        nullable=False, 
        server_default=func.now(),
        comment="When the account was opened"
    )
    
    last_activity = Column(
        DateTime, 
        nullable=True,
        onupdate=func.now(),
        comment="Timestamp of last account activity"
    )
    
    last_interest_calculation = Column(
        DateTime,
        nullable=True,
        comment="When interest was last calculated and applied"
    )
    
    closed_date = Column(
        DateTime,
        nullable=True,
        comment="When the account was closed (if applicable)"
    )
    
    maturity_date = Column(
        Date,
        nullable=True,
        comment="Maturity date for time-based accounts (CDs, etc.)"
    )
    
    # ===== Limits and Settings =====
    overdraft_limit = Column(
        Numeric(19, 4), 
        default=Decimal('0.00'), 
        nullable=False,
        comment="Maximum allowed overdraft amount"
    )
    
    interest_rate = Column(
        Numeric(7, 4), 
        default=Decimal('0.0000'), 
        nullable=True,
        comment="Annual interest rate (APY) as a decimal"
    )
    
    daily_transfer_limit = Column(
        Numeric(19, 4),
        nullable=True,
        comment="Maximum daily transfer amount"
    )
    
    withdrawal_limit = Column(
        Numeric(19, 4),
        nullable=True,
        comment="Maximum daily withdrawal amount"
    )
    
    deposit_limit = Column(
        Numeric(19, 4),
        nullable=True,
        comment="Maximum daily deposit amount"
    )
    
    # ===== Metadata and Relationships =====
    metadata_ = Column(
        "metadata", 
        JSON,
        nullable=True,
        default=dict,
        comment="Flexible field for additional account metadata"
    )
    
    user_id = Column(
        UUID, 
        ForeignKey("users.id", ondelete="CASCADE"), 
        nullable=False,
        index=True
    )
    
    # ===== Relationships =====
    user = relationship(
        "User", 
        back_populates="accounts",
        lazy="selectin"
    )
    
    transactions = relationship(
        "Transaction", 
        back_populates="account", 
        cascade="all, delete-orphan",
        lazy="dynamic",
        order_by="desc(Transaction.transaction_date)"
    )
    
    cards = relationship(
        "Card", 
        back_populates="account", 
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    
    beneficiaries = relationship(
        "Beneficiary",
        secondary="account_beneficiaries",
        back_populates="accounts"
    )
    
    standing_orders = relationship(
        "StandingOrder",
        back_populates="account",
        cascade="all, delete-orphan"
    )
    
    direct_debits = relationship(
        "DirectDebit",
        back_populates="account",
        cascade="all, delete-orphan"
    )
    
    # ===== Properties and Methods =====
    @property
    def masked_account_number(self) -> str:
        """Return a masked version of the account number for display."""
        if not self.account_number or len(self.account_number) < 4:
            return "****"
        return f"****{self.account_number[-4:]}"
    
    @property
    def is_active(self) -> bool:
        """Check if the account is currently active."""
        return self.status == AccountStatus.ACTIVE
    
    @property
    def is_overdrawn(self) -> bool:
        """Check if the account is currently overdrawn."""
        return self.current_balance < Decimal('0.00')
    
    @property
    def available_overdraft(self) -> Decimal:
        """Calculate available overdraft amount."""
        if not self.is_overdraft_protected:
            return Decimal('0.00')
        available = self.overdraft_limit + self.current_balance
        return max(Decimal('0.00'), available)
    
    @property
    def days_since_last_activity(self) -> Optional[int]:
        """Return number of days since last account activity."""
        if not self.last_activity:
            return None
        return (datetime.utcnow() - self.last_activity).days
    
    @property
    def days_until_maturity(self) -> Optional[int]:
        """Return number of days until account maturity."""
        if not self.maturity_date:
            return None
        return (self.maturity_date - date.today()).days
    
    def update_balance(self, amount: Decimal, hold: bool = False) -> None:
        """Update the account balance by the specified amount.
        
        Args:
            amount: The amount to add (positive) or subtract (negative)
            hold: If True, place the amount on hold instead of adjusting available balance
        """
        if hold:
            self.hold_balance += amount
        else:
            self.current_balance += amount
            self.available_balance = self.current_balance + self.overdraft_limit - self.hold_balance
            
        self.last_activity = datetime.utcnow()
    
    def clear_hold(self, amount: Optional[Decimal] = None) -> None:
        """Clear a hold on funds.
        
        Args:
            amount: Specific amount to clear (defaults to all held funds)
        """
        if amount is None:
            self.hold_balance = Decimal('0.00')
        else:
            self.hold_balance = max(Decimal('0.00'), self.hold_balance - amount)
        
        self.available_balance = self.current_balance + self.overdraft_limit - self.hold_balance
    
    def calculate_interest(self, as_of: Optional[date] = None) -> Decimal:
        """Calculate interest accrued since last calculation.
        
        Args:
            as_of: Date to calculate interest up to (defaults to today)
            
        Returns:
            Decimal: Amount of interest accrued
        """
        if not self.interest_rate or self.interest_rate <= 0:
            return Decimal('0.00')
            
        as_of = as_of or date.today()
        last_calc = self.last_interest_calculation.date() if self.last_interest_calculation else self.opened_date.date()
        
        if as_of <= last_calc:
            return Decimal('0.00')
            
        days = (as_of - last_calc).days
        if days <= 0:
            return Decimal('0.00')
            
        # Simple interest calculation for now
        daily_rate = Decimal(str(self.interest_rate)) / Decimal('365.0')
        interest = (self.current_balance * daily_rate * Decimal(str(days))).quantize(
            Decimal('0.01'), rounding=ROUND_HALF_UP
        )
        
        return interest
    
    def apply_interest(self) -> Decimal:
        """Calculate and apply interest to the account.
        
        Returns:
            Decimal: Amount of interest applied
        """
        interest = self.calculate_interest()
        if interest > 0:
            self.current_balance += interest
            self.available_balance = self.current_balance + self.overdraft_limit - self.hold_balance
            self.last_interest_calculation = datetime.utcnow()
            self.last_activity = self.last_interest_calculation
        return interest
    
    def can_withdraw(self, amount: Decimal) -> bool:
        """Check if a withdrawal of the specified amount is allowed.
        
        Args:
            amount: Amount to withdraw
            
        Returns:
            bool: True if withdrawal is allowed, False otherwise
        """
        if amount <= 0:
            return False
            
        # Check available balance including overdraft
        if self.available_balance < amount:
            return False
            
        # Check withdrawal limits
        if self.withdrawal_limit and amount > self.withdrawal_limit:
            return False
            
        return True
    
    def can_transfer(self, amount: Decimal) -> bool:
        """Check if a transfer of the specified amount is allowed.
        
        Args:
            amount: Amount to transfer
            
        Returns:
            bool: True if transfer is allowed, False otherwise
        """
        if amount <= 0:
            return False
            
        # Check available balance including overdraft
        if self.available_balance < amount:
            return False
            
        # Check transfer limits
        if self.daily_transfer_limit and amount > self.daily_transfer_limit:
            return False
            
        return True
    
    def close_account(self, reason: str = "Customer request") -> None:
        """Close the account.
        
        Args:
            reason: Reason for account closure
        """
        if self.status in {AccountStatus.CLOSED, AccountStatus.CHARGED_OFF}:
            return
            
        self.status = AccountStatus.CLOSED
        self.closed_date = datetime.utcnow()
        self.metadata_ = self.metadata_ or {}
        self.metadata_["closure_reason"] = reason
        self.metadata_["closure_balance"] = str(self.current_balance)
        self.last_activity = self.closed_date
    
    def freeze_account(self, reason: str) -> None:
        """Freeze the account (no debits allowed).
        
        Args:
            reason: Reason for freezing the account
        """
        if self.status != AccountStatus.ACTIVE:
            return
            
        self.status = AccountStatus.FROZEN
        self.metadata_ = self.metadata_ or {}
        self.metadata_["freeze_reason"] = reason
        self.metadata_["frozen_at"] = datetime.utcnow().isoformat()
    
    def unfreeze_account(self) -> None:
        """Unfreeze a frozen account."""
        if self.status != AccountStatus.FROZEN:
            return
            
        self.status = AccountStatus.ACTIVE
        if self.metadata_ and "freeze_reason" in self.metadata_:
            self.metadata_["unfrozen_at"] = datetime.utcnow().isoformat()
    
    def to_dict(self, include_sensitive: bool = False) -> Dict[str, Any]:
        """Convert account to dictionary representation.
        
        Args:
            include_sensitive: Whether to include sensitive information
            
        Returns:
            Dict containing account data
        """
        data = {
            "id": self.id,
            "account_number": self.masked_account_number,
            "display_name": self.display_name,
            "type": self.account_type.value,
            "status": self.status.value,
            "currency": self.currency,
            "current_balance": float(self.current_balance),
            "available_balance": float(self.available_balance),
            "is_primary": self.is_primary,
            "opened_date": self.opened_date.isoformat() if self.opened_date else None,
            "last_activity": self.last_activity.isoformat() if self.last_activity else None,
            "is_overdraft_protected": self.is_overdraft_protected,
            "overdraft_limit": float(self.overdraft_limit) if self.overdraft_limit else 0.0,
        }
        
        if include_sensitive:
            data.update({
                "full_account_number": self.account_number,
                "interest_rate": float(self.interest_rate) if self.interest_rate else 0.0,
                "daily_transfer_limit": float(self.daily_transfer_limit) if self.daily_transfer_limit else None,
                "withdrawal_limit": float(self.withdrawal_limit) if self.withdrawal_limit else None,
                "hold_balance": float(self.hold_balance),
                "min_balance": float(self.min_balance),
                "maturity_date": self.maturity_date.isoformat() if self.maturity_date else None,
                "is_joint": self.is_joint,
                "metadata": self.metadata_ or {},
            })
            
        return data
    
    def __repr__(self) -> str:
        return (
            f"<Account(id={self.id}, "
            f"type={self.account_type}, "
            f"number={self.masked_account_number}, "
            f"balance={self.current_balance} {self.currency}, "
            f"status={self.status})>"
        )


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
    REWARDS = "rewards"
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
        return card_type in {cls.CREDIT, cls.REWARDS, cls.STUDENT, cls.TRAVEL}
    
    @classmethod
    def is_debit_card(cls, card_type: Union[str, 'CardType']) -> bool:
        """Check if the card type is a debit card."""
        return card_type in {cls.DEBIT, cls.PREPAID, cls.SECURED}
    
    @classmethod
    def is_business_card(cls, card_type: Union[str, 'CardType']) -> bool:
        """Check if the card is for business use."""
        return card_type in {cls.BUSINESS, cls.CORPORATE, cls.FLEET, cls.PURCHASING}


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
    
    @classmethod
    def is_active_status(cls, status: Union[str, 'CardStatus']) -> bool:
        """Check if the status indicates the card is active."""
        return status == cls.ACTIVE
    
    @classmethod
    def is_blocked_status(cls, status: Union[str, 'CardStatus']) -> bool:
        """Check if the status indicates the card is blocked."""
        return status in {cls.BLOCKED, cls.SUSPENDED, cls.LOST, cls.STOLEN, cls.COMPROMISED}
    
    @classmethod
    def is_permanent_status(cls, status: Union[str, 'CardStatus']) -> bool:
        """Check if the status is permanent (cannot be reactivated)."""
        return status in {cls.CLOSED, cls.DESTROYED, cls.EXPIRED}


class Card(ModelBase):
    """Payment card linked to an account with comprehensive features.
    
    This model represents a physical or virtual payment card that can be used
    for transactions, with support for various card types, limits, and security features.
    """
    
    __tablename__ = "cards"
    
    # Primary key
    id = Column(UUID, primary_key=True, default=uuid4, index=True, unique=True, nullable=False,
              comment='Unique identifier for the card')
    
    __table_args__ = (
        # Core indexes
        Index('idx_card_account', 'account_id', 'status'),
        Index('idx_card_number', 'card_number', unique=True),
        Index('idx_card_expiry', 'expiry_year', 'expiry_month'),
        
        # Check constraints
        CheckConstraint('expiry_month BETWEEN 1 AND 12', name='check_valid_expiry_month'),
        CheckConstraint('expiry_year >= 2000', name='check_valid_expiry_year'),
        CheckConstraint('daily_limit >= 0', name='check_daily_limit_non_negative'),
        CheckConstraint('transaction_limit >= 0', name='check_txn_limit_non_negative'),
        CheckConstraint('pos_limit >= 0', name='check_pos_limit_non_negative'),
        CheckConstraint('atm_limit >= 0', name='check_atm_limit_non_negative'),
        CheckConstraint('(pin_attempts_remaining >= 0) AND (pin_attempts_remaining <= 3)', 
                       name='check_pin_attempts_range'),
        CheckConstraint('(closed_date IS NULL) OR (closed_date >= issued_date)',
                      name='check_closed_after_issued'),
    )
    
    # ===== Card Identification =====
    card_number = Column(
        String(16), 
        nullable=False, 
        index=True,
        comment="Last 4 digits of the card number (full number is encrypted)"
    )
    
    card_holder_name = Column(
        String(100), 
        nullable=False,
        comment="Cardholder name as it appears on the card"
    )
    
    # ===== Card Details =====
    card_type = Column(
        SQLEnum(CardType), 
        nullable=False,
        index=True,
        comment="Type of card (debit, credit, etc.)"
    )
    
    expiry_month = Column(
        Integer, 
        nullable=False,
        comment="Expiration month (1-12)"
    )
    
    expiry_year = Column(
        Integer, 
        nullable=False,
        comment="Expiration year (4 digits)"
    )
    
    cvv = Column(
        String(4), 
        nullable=True,  # Not stored for security, only used during transactions
        comment="Card verification value (hashed in secure storage)"
    )
    
    # ===== Status and Flags =====
    status = Column(
        SQLEnum(CardStatus), 
        default=CardStatus.PENDING_ACTIVATION, 
        nullable=False,
        index=True,
        comment="Current status of the card"
    )
    
    is_contactless = Column(
        Boolean, 
        default=True, 
        nullable=False,
        comment="Whether contactless payments are enabled"
    )
    
    is_virtual = Column(
        Boolean, 
        default=False, 
        nullable=False,
        comment="Whether this is a virtual/digital card"
    )
    
    is_primary = Column(
        Boolean,
        default=False,
        nullable=False,
        comment="Whether this is the primary card for the account"
    )
    
    # ===== Limits and Controls =====
    daily_limit = Column(
        Numeric(19, 4), 
        nullable=True,
        comment="Maximum daily spending limit (null for account default)"
    )
    
    transaction_limit = Column(
        Numeric(19, 4), 
        nullable=True,
        comment="Maximum per-transaction limit (null for account default)"
    )
    
    pos_limit = Column(
        Numeric(19, 4),
        nullable=True,
        comment="Point of Sale (retail) transaction limit"
    )
    
    atm_limit = Column(
        Numeric(19, 4),
        nullable=True,
        comment="Daily ATM withdrawal limit"
    )
    
    international_limit = Column(
        Numeric(19, 4),
        nullable=True,
        comment="International transaction limit"
    )
    
    # ===== Security =====
    pin_attempts_remaining = Column(
        Integer,
        default=3,
        nullable=False,
        comment="Number of PIN attempts remaining before card is blocked"
    )
    
    last_pin_change = Column(
        DateTime,
        nullable=True,
        comment="When the PIN was last changed"
    )
    
    # ===== Metadata =====
    issued_date = Column(
        DateTime, 
        nullable=False, 
        server_default=func.now(),
        comment="When the card was issued"
    )
    
    activation_date = Column(
        DateTime,
        nullable=True,
        comment="When the card was activated"
    )
    
    last_used = Column(
        DateTime, 
        nullable=True,
        onupdate=func.now(),
        comment="When the card was last used"
    )
    
    closed_date = Column(
        DateTime,
        nullable=True,
        comment="When the card was closed/cancelled"
    )
    
    metadata_ = Column(
        "metadata",
        JSON,  # Using JSON instead of JSONB for database-agnostic compatibility
        nullable=True,
        default=dict,
        comment="Additional card metadata and settings"
    )
    
    # ===== Relationships =====
    account_id = Column(
        UUID, 
        ForeignKey("accounts.id", ondelete="CASCADE"), 
        nullable=False,
        index=True
    )
    
    account = relationship(
        "Account", 
        back_populates="cards",
        lazy="selectin"
    )
    
    transactions = relationship(
        "Transaction",
        back_populates="card",
        cascade="all, delete-orphan",
        lazy="dynamic",
        order_by="desc(Transaction.transaction_date)"
    )
    
    # ===== Properties and Methods =====
    @property
    def masked_number(self) -> str:
        """Return a masked version of the card number for display."""
        if not self.card_number or len(self.card_number) < 4:
            return "**** **** **** ****"
        return f"**** **** **** {self.card_number[-4:]}"
    
    @property
    def expiry_date(self) -> str:
        """Return formatted expiry date (MM/YY)."""
        return f"{self.expiry_month:02d}/{self.expiry_year % 100:02d}"
    
    @property
    def is_active(self) -> bool:
        """Check if the card is active and not expired."""
        return self.status == CardStatus.ACTIVE and not self.is_expired()
    
    @property
    def is_expired(self) -> bool:
        """Check if the card is expired."""
        current_year = datetime.utcnow().year
        current_month = datetime.utcnow().month
        return (
            self.expiry_year < current_year or 
            (self.expiry_year == current_year and self.expiry_month < current_month)
        )
    
    @property
    def days_until_expiry(self) -> Optional[int]:
        """Return number of days until card expiration."""
        if self.is_expired:
            return 0
            
        expiry_date = date(self.expiry_year, self.expiry_month, 1)
        # Set to last day of expiry month
        if self.expiry_month == 12:
            expiry_date = date(self.expiry_year + 1, 1, 1) - timedelta(days=1)
        else:
            expiry_date = date(self.expiry_year, self.expiry_month + 1, 1) - timedelta(days=1)
            
        return (expiry_date - date.today()).days
    
    def activate(self) -> None:
        """Activate the card."""
        if self.status == CardStatus.PENDING_ACTIVATION:
            self.status = CardStatus.ACTIVE
            self.activation_date = datetime.utcnow()
    
    def block(self, reason: str = "Security concern") -> None:
        """Block the card.
        
        Args:
            reason: Reason for blocking the card
        """
        if self.status in {CardStatus.BLOCKED, CardStatus.CLOSED, CardStatus.EXPIRED}:
            return
            
        self.status = CardStatus.BLOCKED
        self.metadata_ = self.metadata_ or {}
        self.metadata_["block_reason"] = reason
        self.metadata_["blocked_at"] = datetime.utcnow().isoformat()
    
    def unblock(self) -> None:
        """Unblock a blocked card."""
        if self.status == CardStatus.BLOCKED:
            self.status = CardStatus.ACTIVE
            if self.metadata_ and "block_reason" in self.metadata_:
                self.metadata_["unblocked_at"] = datetime.utcnow().isoformat()
    
    def close(self, reason: str = "Cardholder request") -> None:
        """Close the card permanently.
        
        Args:
            reason: Reason for closing the card
        """
        if self.status in {CardStatus.CLOSED, CardStatus.DESTROYED}:
            return
            
        self.status = CardStatus.CLOSED
        self.closed_date = datetime.utcnow()
        self.metadata_ = self.metadata_ or {}
        self.metadata_["closure_reason"] = reason
    
    def report_lost_or_stolen(self, is_stolen: bool = False) -> None:
        """Report the card as lost or stolen.
        
        Args:
            is_stolen: Whether the card was stolen (vs. just lost)
        """
        new_status = CardStatus.STOLEN if is_stolen else CardStatus.LOST
        if self.status != new_status:
            self.status = new_status
            self.metadata_ = self.metadata_ or {}
            self.metadata_[f"reported_{'stolen' if is_stolen else 'lost'}_at"] = datetime.utcnow().isoformat()
    
    def verify_pin(self, pin_attempt: str) -> bool:
        """Verify a PIN attempt.
        
        Args:
            pin_attempt: The PIN to verify
            
        Returns:
            bool: True if PIN is correct, False otherwise
        """
        # In a real implementation, this would verify against a hashed PIN
        # For security, actual PIN verification would be handled by a dedicated service
        if self.pin_attempts_remaining <= 0:
            self.status = CardStatus.BLOCKED
            self.metadata_ = self.metadata_ or {}
            self.metadata_["blocked_due_to_pin_failures"] = True
            return False
            
        # This is a placeholder - actual implementation would verify against hashed PIN
        is_correct = False  # Replace with actual verification
        
        if not is_correct:
            self.pin_attempts_remaining -= 1
            if self.pin_attempts_remaining <= 0:
                self.status = CardStatus.BLOCKED
                self.metadata_ = self.metadata_ or {}
                self.metadata_["blocked_due_to_pin_failures"] = True
            return False
            
        # Reset attempts on successful verification
        self.pin_attempts_remaining = 3
        return True
    
    def update_pin(self, new_pin: str) -> None:
        """Update the card's PIN.
        
        Args:
            new_pin: The new PIN to set
        """
        # In a real implementation, this would hash the PIN before storage
        # For security, actual PIN updates would be handled by a dedicated service
        self.last_pin_change = datetime.utcnow()
        self.pin_attempts_remaining = 3
        
    def can_use_for_transaction(self, amount: Decimal, transaction_type: str = "purchase") -> bool:
        """Check if the card can be used for a transaction.
        
        Args:
            amount: Transaction amount
            transaction_type: Type of transaction (purchase, withdrawal, etc.)
            
        Returns:
            bool: True if the transaction is allowed, False otherwise
        """
        if not self.is_active:
            return False
            
        # Check transaction-specific limits
        if transaction_type == "withdrawal" and self.atm_limit and amount > self.atm_limit:
            return False
            
        if transaction_type == "purchase" and self.pos_limit and amount > self.pos_limit:
            return False
            
        # Check general transaction limit
        if self.transaction_limit and amount > self.transaction_limit:
            return False
            
        # Additional checks could be added here (e.g., velocity checks, merchant category blocks)
        return True
    
    def to_dict(self, include_sensitive: bool = False) -> Dict[str, Any]:
        """Convert card to dictionary representation.
        
        Args:
            include_sensitive: Whether to include sensitive information
            
        Returns:
            Dict containing card data
        """
        data = {
            "id": self.id,
            "masked_number": self.masked_number,
            "card_holder_name": self.card_holder_name,
            "card_type": self.card_type.value,
            "expiry_date": self.expiry_date,
            "status": self.status.value,
            "is_active": self.is_active,
            "is_virtual": self.is_virtual,
            "is_contactless": self.is_contactless,
            "issued_date": self.issued_date.isoformat() if self.issued_date else None,
            "days_until_expiry": self.days_until_expiry,
            "account_id": self.account_id,
        }
        
        if include_sensitive:
            data.update({
                "full_card_number": self.card_number,  # In real implementation, this would be encrypted
                "cvv": self.cvv,  # In real implementation, this would never be exposed
                "daily_limit": float(self.daily_limit) if self.daily_limit else None,
                "transaction_limit": float(self.transaction_limit) if self.transaction_limit else None,
                "pos_limit": float(self.pos_limit) if self.pos_limit else None,
                "atm_limit": float(self.atm_limit) if self.atm_limit else None,
                "international_limit": float(self.international_limit) if self.international_limit else None,
                "pin_attempts_remaining": self.pin_attempts_remaining,
                "metadata": self.metadata_ or {},
            })
            
        return data
    
    def __repr__(self) -> str:
        return (
            f"<Card(id={self.id}, "
            f"type={self.card_type}, "
            f"number={self.masked_number}, "
            f"expires={self.expiry_date}, "
            f"status={self.status})>"
        )
