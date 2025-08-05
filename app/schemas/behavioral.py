"""
Behavioral analysis schemas.
"""

from typing import List, Optional, Dict, Any
from datetime import date, datetime
from enum import Enum
from pydantic import BaseModel, Field, ConfigDict

from .base import BaseSchema, TimestampMixin, IDSchemaMixin

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

class Transaction(BaseModel):
    """Transaction model for behavioral analysis."""
    id: str
    amount: float
    date: str
    category: str
    description: str
    type: str  # 'credit' or 'debit'

class BehavioralInsight(BaseModel):
    """Behavioral insight model."""
    insight_type: str
    description: str
    confidence: float = Field(..., ge=0, le=1)
    impact: str = "neutral"  # 'positive', 'negative', or 'neutral'
    metadata: Optional[Dict[str, Any]] = None

class BehavioralAnalysisRequest(BaseModel):
    """Request model for behavioral analysis."""
    customer_id: str
    transactions: List[Transaction]
    time_period: str = "30d"
    include_insights: bool = True
    include_recommendations: bool = True

class BehavioralAnalysisResponse(BaseModel):
    """Response model for behavioral analysis."""
    customer_id: str
    time_period: str
    total_transactions: int
    total_spent: float
    total_income: float
    spending_categories: Dict[str, float]
    behavioral_insights: List[BehavioralInsight]
    recommendations: Optional[List[str]] = None

# Behavioral Pattern Schemas
class BehavioralPatternBase(BaseSchema):
    """Base schema for behavioral patterns."""
    user_id: Optional[int] = None
    pattern_type: BehavioralPatternType
    analysis_period_start: date
    analysis_period_end: date
    spending_categories: Optional[Dict[str, Any]] = None
    monthly_average_spending: Optional[float] = None
    spending_volatility: Optional[float] = None
    seasonal_patterns: Optional[Dict[str, Any]] = None
    behavioral_biases: Optional[Dict[str, Any]] = None
    risk_indicators: Optional[Dict[str, Any]] = None
    spending_trends: Optional[Dict[str, Any]] = None
    unusual_patterns: Optional[Dict[str, Any]] = None
    
    model_config = ConfigDict(from_attributes=True)

class BehavioralPatternCreate(BehavioralPatternBase):
    """Schema for creating a new behavioral pattern."""
    user_id: int
    pattern_type: BehavioralPatternType
    analysis_period_start: date
    analysis_period_end: date

class BehavioralPatternUpdate(BehavioralPatternBase):
    """Schema for updating an existing behavioral pattern."""
    pattern_type: Optional[BehavioralPatternType] = None
    analysis_period_start: Optional[date] = None
    analysis_period_end: Optional[date] = None

class BehavioralPattern(BehavioralPatternBase, IDSchemaMixin, TimestampMixin):
    """Complete behavioral pattern schema."""
    pattern_id: int
    
    class Config:
        from_attributes = True
