"""
AI-related models for recommendations, behavioral patterns, and fraud detection.
"""
from enum import Enum
from datetime import datetime, time
from decimal import Decimal
from typing import Optional, List, Dict, Any

from sqlalchemy import (
    Column, String, Integer, Boolean, JSON, 
    ForeignKey, DateTime, Numeric, Text, Index
)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import ARRAY, JSONB

from .base import ModelBase


class RecommendationType(str, Enum):
    """Types of AI-generated recommendations."""
    SAVINGS = "savings"
    INVESTMENT = "investment"
    CREDIT_CARD = "credit_card"
    LOAN = "loan"
    INSURANCE = "insurance"
    BUDGETING = "budgeting"
    SPENDING = "spending"
    FINANCIAL_GOAL = "financial_goal"
    OTHER = "other"


class RecommendationStatus(str, Enum):
    """Status of a recommendation."""
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    IMPLEMENTED = "implemented"
    EXPIRED = "expired"


class AIRecommendation(ModelBase):
    """AI-generated financial recommendations for users."""
    
    __tablename__ = "ai_recommendations"
    
    # Recommendation details
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    recommendation_type = Column(SQLEnum(RecommendationType), nullable=False)
    status = Column(SQLEnum(RecommendationStatus), default=RecommendationStatus.PENDING, nullable=False)
    
    # AI metadata
    confidence_score = Column(Numeric(5, 4), nullable=True)  # 0.0 to 1.0
    model_version = Column(String(50), nullable=True)
    features_used = Column(JSON, nullable=True)  # Features used for this recommendation
    
    # Action details
    action_url = Column(String(512), nullable=True)
    action_text = Column(String(100), nullable=True)
    
    # Expiration and timing
    valid_until = Column(DateTime, nullable=True)
    shown_at = Column(DateTime, nullable=True)
    actioned_at = Column(DateTime, nullable=True)
    
    # User relationship
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    user = relationship("User", back_populates="ai_recommendations")
    
    # Related account (if applicable)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=True)
    account = relationship("Account")
    
    # Additional metadata
    metadata_ = Column("metadata", JSON, nullable=True)
    
    # Indexes
    __table_args__ = (
        Index('idx_recommendation_user', 'user_id', 'status'),
        Index('idx_recommendation_type', 'recommendation_type', 'status'),
    )
    
    @property
    def is_active(self) -> bool:
        """Check if the recommendation is still active."""
        if self.status != RecommendationStatus.PENDING:
            return False
        if self.valid_until and self.valid_until < datetime.utcnow():
            return False
        return True
    
    def __repr__(self) -> str:
        return f"<AIRecommendation(id={self.id}, type={self.recommendation_type}, status={self.status})>"


class BehavioralPatternType(str, Enum):
    """Types of behavioral patterns detected by AI."""
    SPENDING = "spending"
    INCOME = "income"
    SAVINGS = "savings"
    TRANSACTION_TIMING = "transaction_timing"
    LOCATION = "location"
    DEVICE_USAGE = "device_usage"
    LOGIN_PATTERN = "login_pattern"
    APP_USAGE = "app_usage"
    CASH_FLOW = "cash_flow"
    RISK_APPETITE = "risk_appetite"


class BehavioralPattern(ModelBase):
    """AI-detected behavioral patterns for users."""
    
    __tablename__ = "behavioral_patterns"
    
    # Pattern identification
    pattern_type = Column(SQLEnum(BehavioralPatternType), nullable=False, index=True)
    pattern_name = Column(String(100), nullable=False)
    
    # Pattern details
    description = Column(Text, nullable=False)
    confidence_score = Column(Numeric(5, 4), nullable=True)  # 0.0 to 1.0
    
    # Pattern data (flexible schema based on pattern type)
    pattern_data = Column(JSONB, nullable=False)
    
    # Time period this pattern was detected for
    start_date = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)
    
    # AI metadata
    model_version = Column(String(50), nullable=True)
    detected_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # User relationship
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    user = relationship("User", back_populates="behavioral_patterns")
    
    # Related account (if applicable)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=True)
    account = relationship("Account")
    
    # Indexes
    __table_args__ = (
        Index('idx_behavioral_user_type', 'user_id', 'pattern_type'),
        Index('idx_behavioral_detected', 'detected_at'),
    )
    
    def __repr__(self) -> str:
        return f"<BehavioralPattern(id={self.id}, type={self.pattern_type}, user_id={self.user_id})>"


class FraudAlertSeverity(str, Enum):
    """Severity levels for fraud alerts."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class FraudAlertStatus(str, Enum):
    """Status of a fraud alert."""
    OPEN = "open"
    INVESTIGATING = "investigating"
    RESOLVED = "resolved"
    FALSE_POSITIVE = "false_positive"
    CONFIRMED_FRAUD = "confirmed_fraud"


class FraudAlert(ModelBase):
    """Fraud detection alerts generated by AI systems."""
    
    __tablename__ = "fraud_alerts"
    
    # Alert details
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    
    # Severity and status
    severity = Column(SQLEnum(FraudAlertSeverity), nullable=False, index=True)
    status = Column(SQLEnum(FraudAlertStatus), default=FraudAlertStatus.OPEN, nullable=False, index=True)
    
    # AI metadata
    confidence_score = Column(Numeric(5, 4), nullable=True)  # 0.0 to 1.0
    model_version = Column(String(50), nullable=True)
    features_used = Column(JSON, nullable=True)
    
    # Related transaction (if applicable)
    transaction_id = Column(Integer, ForeignKey("transactions.id"), nullable=True)
    transaction = relationship("Transaction")
    
    # Related account
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False, index=True)
    account = relationship("Account")
    
    # User relationship
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    user = relationship("User", back_populates="fraud_alerts")
    
    # Resolution details
    resolved_at = Column(DateTime, nullable=True)
    resolved_by = Column(Integer, ForeignKey("employees.id"), nullable=True)
    resolution_notes = Column(Text, nullable=True)
    
    # Additional metadata
    metadata_ = Column("metadata", JSON, nullable=True)
    
    # Indexes
    __table_args__ = (
        Index('idx_fraud_alert_status', 'status', 'severity'),
        Index('idx_fraud_alert_user', 'user_id', 'status'),
    )
    
    @property
    def is_resolved(self) -> bool:
        """Check if the alert has been resolved."""
        return self.status in [
            FraudAlertStatus.RESOLVED,
            FraudAlertStatus.FALSE_POSITIVE,
            FraudAlertStatus.CONFIRMED_FRAUD
        ]
    
    def resolve(self, status: FraudAlertStatus, notes: str, resolved_by: int) -> None:
        """Mark the alert as resolved."""
        self.status = status
        self.resolution_notes = notes
        self.resolved_by = resolved_by
        self.resolved_at = datetime.utcnow()
    
    def __repr__(self) -> str:
        return f"<FraudAlert(id={self.id}, severity={self.severity}, status={self.status})>"
