"""
Transaction model for financial transactions.
"""
from enum import Enum
from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import (
    Column, String, Numeric, DateTime, Integer, 
    ForeignKey, Enum as SQLEnum, Boolean, Text, Index, JSON
)
from sqlalchemy.orm import relationship

from .base import ModelBase


class TransactionType(str, Enum):
    """Types of financial transactions."""
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
    """Transaction status values."""
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REVERSED = "reversed"
    HOLD = "hold"
    CANCELLED = "cancelled"


class TransactionCategory(str, Enum):
    """Transaction categories for better classification."""
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


class Transaction(ModelBase):
    """Financial transaction model."""
    
    __tablename__ = "transactions"
    
    # Primary Key
    id = Column(Integer, primary_key=True, autoincrement=True)
    # Identification
    reference_id = Column(String(64), unique=True, nullable=False, index=True)
    
    # Transaction details
    amount = Column(Numeric(19, 4), nullable=False)
    currency = Column(String(3), default="INR", nullable=False)
    transaction_type = Column(SQLEnum(TransactionType), nullable=False)
    category = Column(SQLEnum(TransactionCategory), nullable=True)
    description = Column(Text, nullable=True)
    
    # Status and timing
    status = Column(SQLEnum(TransactionStatus), default=TransactionStatus.PENDING, nullable=False)
    transaction_date = Column(DateTime, nullable=False, index=True)
    posted_date = Column(DateTime, nullable=True)
    
    # Account relationships
    account_id = Column(Integer, ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False, index=True)
    account = relationship("Account", back_populates="transactions")
    
    # Counterparty information
    counterparty_name = Column(String(255), nullable=True)
    counterparty_account = Column(String(34), nullable=True)  # IBAN format
    counterparty_ifsc = Column(String(20), nullable=True)
    
    # Location data
    merchant_id = Column(Integer, ForeignKey("merchants.id"), nullable=True)
    merchant = relationship("Merchant", back_populates="transactions")
    location = Column(JSON, nullable=True)  # {latitude: float, longitude: float, address: str}
    
    # Card details for card transactions
    card_id = Column(Integer, ForeignKey("cards.id"), nullable=True)
    card = relationship("Card", back_populates="transactions")
    
    # Additional metadata
    metadata_ = Column("metadata", JSON, nullable=True)  # Flexible field for additional data
    is_recurring = Column(Boolean, default=False, nullable=False)
    is_international = Column(Boolean, default=False, nullable=False)
    
    # Fraud detection flags
    is_flagged = Column(Boolean, default=False, nullable=False)
    fraud_score = Column(Numeric(5, 2), nullable=True)
    
    # Indexes
    __table_args__ = (
        Index('idx_transaction_account_date', 'account_id', 'transaction_date'),
        Index('idx_transaction_reference', 'reference_id', unique=True),
        Index('idx_transaction_type_status', 'transaction_type', 'status'),
        Index('idx_transaction_category', 'category'),
    )
    
    @property
    def is_debit(self) -> bool:
        """Check if this is a debit transaction."""
        return self.amount < 0
    
    @property
    def is_credit(self) -> bool:
        """Check if this is a credit transaction."""
        return self.amount >= 0
    
    @property
    def absolute_amount(self) -> Decimal:
        """Return the absolute value of the transaction amount."""
        return abs(self.amount)
    
    def __repr__(self) -> str:
        return f"<Transaction(id={self.id}, amount={self.amount}, type={self.transaction_type}, status={self.status})>"


class MerchantCategory(str, Enum):
    """Merchant categories for transaction classification."""
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


class Merchant(ModelBase):
    """Merchant information for transactions."""
    
    __tablename__ = "merchants"
    
    # Primary Key
    id = Column(Integer, primary_key=True, autoincrement=True)
    # Merchant identification
    name = Column(String(255), nullable=False, index=True)
    merchant_id = Column(String(50), unique=True, nullable=True)  # External merchant ID
    category = Column(SQLEnum(MerchantCategory), nullable=False, index=True)
    
    # Contact information
    website = Column(String(255), nullable=True)
    phone = Column(String(20), nullable=True)
    email = Column(String(255), nullable=True)
    
    # Location
    address = Column(JSON, nullable=True)  # {street, city, state, country, postal_code, coordinates}
    
    # Additional metadata
    is_online = Column(Boolean, default=False, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    
    # Relationships
    transactions = relationship("Transaction", back_populates="merchant")
    
    def __repr__(self) -> str:
        return f"<Merchant(id={self.id}, name={self.name}, category={self.category})>"
