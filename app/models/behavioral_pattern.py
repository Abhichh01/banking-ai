"""
Behavioral Pattern model for AI-driven customer behavior analysis.
"""
from datetime import date, datetime
from enum import Enum
from typing import Dict, Any, List, Optional
from sqlalchemy import Column, Integer, String, Text, JSON, ForeignKey, DateTime, Date, Float, Index, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func

from .base import ModelBase

class BehavioralPatternType(str, Enum):
    SPENDING_HABIT = "spending_habit"
    INCOME_PATTERN = "income_pattern"
    TRANSACTION_TIMING = "transaction_timing"
    LOCATION_BASED = "location_based"
    DEVICE_USAGE = "device_usage"
    PAYMENT_PREFERENCE = "payment_preference"
    RISK_BEHAVIOR = "risk_behavior"
    SAVINGS_BEHAVIOR = "savings_behavior"
    CREDIT_USAGE = "credit_usage"
    SUBSCRIPTION = "subscription"

class BehavioralPattern(ModelBase):
    """
    Model for storing AI-identified behavioral patterns of users.
    """
    __tablename__ = 'behavioral_patterns'
    
    pattern_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False, index=True)
    pattern_type = Column(SQLEnum(BehavioralPatternType), nullable=False, index=True)
    
    # Analysis period
    analysis_period_start = Column(Date, nullable=False, index=True)
    analysis_period_end = Column(Date, nullable=False, index=True)
    
    # Pattern data (stored as JSON for flexibility)
    spending_categories = Column(JSONB)  # Category-wise spending distribution
    monthly_average_spending = Column(Float)  # Average monthly spending
    spending_volatility = Column(Float)  # Coefficient of variation (0-1)
    seasonal_patterns = Column(JSONB)  # Month/week/day patterns
    behavioral_biases = Column(JSONB)  # Detected cognitive biases
    risk_indicators = Column(JSONB)  # Risk-related patterns
    spending_trends = Column(JSONB)  # Trend analysis over time
    unusual_patterns = Column(JSONB)  # Anomalies and outliers
    
    # AI Analysis
    confidence_score = Column(Float, nullable=False)  # 0-1 scale
    ai_insights = Column(JSONB)  # AI-generated insights
    recommendations = Column(JSONB)  # Personalized recommendations
    
    # Metadata
    next_analysis_date = Column(Date, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="behavioral_patterns")
    
    # Indexes
    __table_args__ = (
        Index('idx_behavioral_user_pattern', 'user_id', 'pattern_type'),
        Index('idx_analysis_period', 'analysis_period_start', 'analysis_period_end'),
        Index('idx_confidence_score', 'confidence_score'),
        Index('idx_next_analysis', 'next_analysis_date'),
    )
    
    def __repr__(self) -> str:
        return f"<BehavioralPattern {self.pattern_type} for user {self.user_id}>"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary."""
        return {
            'pattern_id': self.pattern_id,
            'user_id': self.user_id,
            'pattern_type': self.pattern_type.value if self.pattern_type else None,
            'analysis_period': {
                'start': self.analysis_period_start.isoformat() if self.analysis_period_start else None,
                'end': self.analysis_period_end.isoformat() if self.analysis_period_end else None
            },
            'spending_analysis': {
                'categories': self.spending_categories,
                'monthly_average': self.monthly_average_spending,
                'volatility': self.spending_volatility,
                'trends': self.spending_trends
            },
            'behavioral_insights': {
                'seasonal_patterns': self.seasonal_patterns,
                'behavioral_biases': self.behavioral_biases,
                'risk_indicators': self.risk_indicators,
                'unusual_patterns': self.unusual_patterns
            },
            'ai_analysis': {
                'confidence_score': self.confidence_score,
                'insights': self.ai_insights,
                'recommendations': self.recommendations
            },
            'next_analysis_date': self.next_analysis_date.isoformat() if self.next_analysis_date else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @classmethod
    def get_latest_for_user(cls, session, user_id: int, pattern_type: Optional[BehavioralPatternType] = None):
        """Get the latest behavioral pattern for a user, optionally filtered by type."""
        query = session.query(cls).filter(
            cls.user_id == user_id
        ).order_by(
            cls.analysis_period_end.desc()
        )
        
        if pattern_type:
            query = query.filter(cls.pattern_type == pattern_type)
            
        return query.first()
    
    def is_current(self) -> bool:
        """Check if this pattern is still considered current."""
        if not self.next_analysis_date:
            return False
        return date.today() <= self.next_analysis_date
