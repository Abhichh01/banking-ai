"""
Risk assessment schemas.
"""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field, validator

class RiskLevel(str, Enum):
    """Risk level classification."""
    VERY_LOW = "very_low"
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    VERY_HIGH = "very_high"

class RiskFactor(BaseModel):
    """Individual risk factor with score and explanation."""
    name: str
    score: float = Field(..., ge=0, le=1)
    explanation: str
    category: str  # e.g., 'credit', 'market', 'operational', 'compliance'
    confidence: float = Field(..., ge=0, le=1)
    
    @validator('score')
    def validate_score(cls, v):
        if v < 0 or v > 1:
            raise ValueError('Score must be between 0 and 1')
        return round(v, 2)
    
    @validator('confidence')
    def validate_confidence(cls, v):
        if v < 0 or v > 1:
            raise ValueError('Confidence must be between 0 and 1')
        return round(v, 2)

class RiskAssessmentRequest(BaseModel):
    """Request model for risk assessment."""
    customer_id: str
    transaction_history: List[Dict[str, Any]]
    account_balances: Dict[str, float]
    credit_score: Optional[int] = None
    income: Optional[float] = None
    employment_status: Optional[str] = None
    existing_loans: Optional[List[Dict[str, Any]]] = None
    investment_portfolio: Optional[Dict[str, float]] = None
    risk_preference: Optional[str] = "moderate"  # 'conservative', 'moderate', 'aggressive'
    time_horizon: Optional[str] = "5y"  # e.g., '1y', '5y', '10y'

class RiskAssessmentResponse(BaseModel):
    """Response model for risk assessment."""
    customer_id: str
    overall_risk_score: float = Field(..., ge=0, le=1)
    risk_level: RiskLevel
    risk_factors: List[RiskFactor]
    risk_by_category: Dict[str, float]
    recommendations: List[str]
    last_updated: datetime
    metadata: Dict[str, Any] = {}
    
    @validator('overall_risk_score')
    def validate_overall_risk_score(cls, v):
        if v < 0 or v > 1:
            raise ValueError('Overall risk score must be between 0 and 1')
        return round(v, 2)
    
    @validator('risk_level', pre=True)
    def determine_risk_level(cls, v, values):
        if 'overall_risk_score' in values:
            score = values['overall_risk_score']
            if score < 0.2:
                return RiskLevel.VERY_LOW
            elif score < 0.4:
                return RiskLevel.LOW
            elif score < 0.7:
                return RiskLevel.MODERATE
            elif score < 0.9:
                return RiskLevel.HIGH
            else:
                return RiskLevel.VERY_HIGH
        return v
