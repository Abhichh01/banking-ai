"""Card model for managing payment cards in the banking system."""
from datetime import datetime, timedelta
from enum import Enum as PyEnum
from typing import Optional, List, Dict, Any
from uuid import uuid4

from sqlalchemy import (
    Column, String, Boolean, DateTime, Integer, ForeignKey, 
    Enum as SQLEnum, Numeric, CheckConstraint, Index, func, text
)
from sqlalchemy.orm import relationship, Mapped

# Import database-agnostic types
from app.db.types import JSON, UUID, Interval
from app.core.security import encrypt_data, decrypt_data
from .base import ModelBase

class CardType(str, PyEnum):
    """Types of payment cards."""
    DEBIT = 'debit'
    CREDIT = 'credit'
    PREPAID = 'prepaid'
    VIRTUAL = 'virtual'
    BUSINESS = 'business'
    FLEET = 'fleet'

class CardStatus(str, PyEnum):
    """Status of a payment card."""
    ACTIVE = 'active'
    INACTIVE = 'inactive'
    LOST = 'lost'
    STOLEN = 'stolen'
    EXPIRED = 'expired'
    BLOCKED = 'blocked'
    SUSPENDED = 'suspended'
    PENDING_ACTIVATION = 'pending_activation'
    CLOSED = 'closed'

class CardBrand(str, PyEnum):
    """Card network/brand."""
    VISA = 'visa'
    MASTERCARD = 'mastercard'
    AMEX = 'amex'
    DISCOVER = 'discover'
    RUPAY = 'rupay'
    MAESTRO = 'maestro'
    JCB = 'jcb'
    UNIONPAY = 'unionpay'

class Card(ModelBase):
    """
    Model representing a payment card in the banking system.
    
    This model handles both physical and virtual cards with support for
    various card types (debit, credit, prepaid) and networks (Visa, Mastercard, etc.).
    """
    __tablename__ = 'cards'
    
    # Core Card Information
    id = Column(
        UUID,
        primary_key=True,
        default=uuid4,
        index=True,
        unique=True,
        nullable=False,
        comment='Unique identifier for the card'
    )
    
    # Card Identification
    card_number = Column(
        String(19),
        nullable=False,
        index=True,
        comment='Encrypted card number (last 4 digits only for display)'
    )
    
    card_number_encrypted = Column(
        String(255),
        nullable=False,
        comment='Fully encrypted card number'
    )
    
    last_four = Column(
        String(4),
        nullable=False,
        comment='Last 4 digits of the card number'
    )
    
    expiry_month = Column(
        Integer,
        nullable=False,
        comment='Card expiration month (1-12)'
    )
    
    expiry_year = Column(
        Integer,
        nullable=False,
        comment='Card expiration year (4 digits)'
    )
    
    cvv_encrypted = Column(
        String(255),
        nullable=False,
        comment='Encrypted CVV code'
    )
    
    # Card Details
    card_type = Column(
        SQLEnum(CardType, name='card_type_enum'),
        nullable=False,
        comment='Type of card (debit, credit, etc.)'
    )
    
    card_brand = Column(
        SQLEnum(CardBrand, name='card_brand_enum'),
        nullable=False,
        comment='Card network/brand (Visa, Mastercard, etc.)'
    )
    
    status = Column(
        SQLEnum(CardStatus, name='card_status_enum'),
        nullable=False,
        default=CardStatus.PENDING_ACTIVATION,
        comment='Current status of the card'
    )
    
    # Cardholder Information
    cardholder_name = Column(
        String(100),
        nullable=False,
        comment='Name of the cardholder as it appears on the card'
    )
    
    # Account and User Relationships
    account_id = Column(
        UUID,
        ForeignKey('accounts.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
        comment='Reference to the account this card is linked to'
    )
    
    user_id = Column(
        UUID,
        ForeignKey('users.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
        comment='Reference to the user who owns this card'
    )
    
    # Limits and Controls
    daily_spend_limit = Column(
        Numeric(19, 4),
        nullable=True,
        comment='Maximum allowed spending per day'
    )
    
    transaction_limit = Column(
        Numeric(19, 4),
        nullable=True,
        comment='Maximum allowed per transaction'
    )
    
    monthly_spend_limit = Column(
        Numeric(19, 4),
        nullable=True,
        comment='Maximum allowed spending per month'
    )
    
    international_enabled = Column(
        Boolean,
        default=False,
        nullable=False,
        comment='Whether international transactions are allowed'
    )
    
    contactless_enabled = Column(
        Boolean,
        default=True,
        nullable=False,
        comment='Whether contactless payments are enabled'
    )
    
    online_payments_enabled = Column(
        Boolean,
        default=True,
        nullable=False,
        comment='Whether online payments are allowed'
    )
    
    atm_withdrawals_enabled = Column(
        Boolean,
        default=True,
        nullable=False,
        comment='Whether ATM withdrawals are allowed'
    )
    
    # Card Metadata
    issue_date = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        comment='Date when the card was issued'
    )
    
    activation_date = Column(
        DateTime(timezone=True),
        nullable=True,
        comment='Date when the card was activated'
    )
    
    expiry_date = Column(
        DateTime(timezone=True),
        nullable=False,
        comment='Date when the card expires'
    )
    
    last_used = Column(
        DateTime(timezone=True),
        nullable=True,
        comment='Date and time when the card was last used'
    )
    
    # Security Features
    pin_encrypted = Column(
        String(255),
        nullable=True,
        comment='Encrypted PIN for the card'
    )
    
    pin_retry_attempts = Column(
        Integer,
        default=0,
        nullable=False,
        comment='Number of failed PIN attempts'
    )
    
    pin_blocked_until = Column(
        DateTime(timezone=True),
        nullable=True,
        comment='Until when the PIN is blocked due to too many failed attempts'
    )
    
    # Additional Data
    metadata_ = Column(
        'metadata',
        JSON,
        nullable=True,
        default=dict,
        comment='Additional metadata for the card'
    )
    
    # Relationships
    account: Mapped['Account'] = relationship(
        'Account', 
        back_populates='cards',
        foreign_keys=[account_id]
    )
    
    user: Mapped['User'] = relationship(
        'User', 
        back_populates='cards',
        foreign_keys=[user_id]
    )
    
    transactions: Mapped[List['Transaction']] = relationship(
        'Transaction',
        back_populates='card',
        cascade='all, delete-orphan',
        passive_deletes=True
    )
    
    # Table Configuration
    __table_args__ = (
        # Core indexes
        Index('idx_card_account', 'account_id', 'status'),
        Index('idx_card_user', 'user_id', 'status'),
        Index('idx_card_expiry', 'expiry_date', 'status'),
        
        # Check constraints
        CheckConstraint('expiry_month BETWEEN 1 AND 12', name='check_valid_expiry_month'),
        CheckConstraint('expiry_year >= 2000', name='check_valid_expiry_year'),
        CheckConstraint('daily_spend_limit IS NULL OR daily_spend_limit >= 0', 
                       name='check_positive_daily_limit'),
        CheckConstraint('transaction_limit IS NULL OR transaction_limit >= 0', 
                       name='check_positive_transaction_limit'),
        CheckConstraint('monthly_spend_limit IS NULL OR monthly_spend_limit >= 0', 
                       name='check_positive_monthly_limit'),
        CheckConstraint('pin_retry_attempts BETWEEN 0 AND 10', 
                       name='check_pin_retry_range'),
        
        # Conditional checks
        CheckConstraint(
            "(status = 'ACTIVE' AND activation_date IS NOT NULL) OR "
            "(status != 'ACTIVE' AND activation_date IS NULL) OR "
            "(status = 'PENDING_ACTIVATION' AND activation_date IS NULL)",
            name='check_activation_status_consistency'
        ),
        
        # Expiry date must be after issue date
        CheckConstraint(
            "expiry_date > issue_date",
            name='check_expiry_after_issue'
        )
    )
    
    def __init__(self, **kwargs):
        """Initialize a new card with proper encryption."""
        super().__init__(**kwargs)
        
        # Encrypt sensitive data if provided
        if 'card_number' in kwargs and kwargs['card_number']:
            self.set_card_number(kwargs['card_number'])
            
        if 'cvv' in kwargs and kwargs['cvv']:
            self.set_cvv(kwargs['cvv'])
            
        if 'pin' in kwargs and kwargs['pin']:
            self.set_pin(kwargs['pin'])
    
    def set_card_number(self, card_number: str):
        """Securely store the card number with encryption."""
        self.card_number = f"•••• •••• •••• {card_number[-4:]}"
        self.card_number_encrypted = encrypt_data(card_number)
        self.last_four = card_number[-4:]
    
    def get_card_number(self) -> Optional[str]:
        """Retrieve the decrypted card number."""
        if not self.card_number_encrypted:
            return None
        return decrypt_data(self.card_number_encrypted)
    
    def set_cvv(self, cvv: str):
        """Securely store the CVV with encryption."""
        self.cvv_encrypted = encrypt_data(cvv)
    
    def get_cvv(self) -> Optional[str]:
        """Retrieve the decrypted CVV."""
        if not self.cvv_encrypted:
            return None
        return decrypt_data(self.cvv_encrypted)
    
    def set_pin(self, pin: str):
        """Securely store the PIN with encryption."""
        self.pin_encrypted = encrypt_data(pin)
    
    def verify_pin(self, pin: str) -> bool:
        """Verify the provided PIN against the stored one."""
        if not self.pin_encrypted:
            return False
        return pin == decrypt_data(self.pin_encrypted)
    
    def is_active(self) -> bool:
        """Check if the card is currently active."""
        now = datetime.utcnow()
        return (
            self.status == CardStatus.ACTIVE and
            self.expiry_date > now and
            (self.pin_blocked_until is None or self.pin_blocked_until < now)
        )
    
    def block_pin(self, minutes: int = 30):
        """Block the PIN for the specified number of minutes."""
        self.pin_blocked_until = datetime.utcnow() + timedelta(minutes=minutes)
    
    def reset_pin_attempts(self):
        """Reset the PIN attempt counter."""
        self.pin_retry_attempts = 0
        self.pin_blocked_until = None
    
    def record_failed_pin_attempt(self, max_attempts: int = 3, block_minutes: int = 30):
        """Record a failed PIN attempt and block if necessary."""
        self.pin_retry_attempts += 1
        
        if self.pin_retry_attempts >= max_attempts:
            self.block_pin(block_minutes)
            return False
        return True
    
    def activate(self):
        """Activate the card."""
        self.status = CardStatus.ACTIVE
        self.activation_date = datetime.utcnow()
    
    def deactivate(self, reason: str = None):
        """Deactivate the card with an optional reason."""
        self.status = CardStatus.INACTIVE
        if reason:
            if not self.metadata_:
                self.metadata_ = {}
            self.metadata_['deactivation_reason'] = reason
    
    def is_expired(self) -> bool:
        """Check if the card has expired."""
        return datetime.utcnow() > self.expiry_date
    
    def get_available_balance(self) -> float:
        """Get the available balance for this card."""
        if not hasattr(self, 'account') or not self.account:
            return 0.0
        return float(self.account.available_balance)
    
    def can_authorize(self, amount: float) -> bool:
        """Check if a transaction for the given amount can be authorized."""
        if not self.is_active():
            return False
            
        # Check against card limits
        if self.transaction_limit and amount > self.transaction_limit:
            return False
            
        # TODO: Check daily/monthly limits (requires transaction history)
        
        # Check account balance for debit cards
        if self.card_type == CardType.DEBIT and amount > self.get_available_balance():
            return False
            
        return True
    
    def __repr__(self) -> str:
        return f"<Card {self.last_four} ({self.card_type}, {self.status})>"
