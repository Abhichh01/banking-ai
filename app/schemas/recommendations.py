"""
Recommendations schemas for financial insights and product suggestions.
"""

from datetime import datetime, date
from typing import List, Optional, Dict, Any, Literal, Union
from enum import Enum
from pydantic import BaseModel, Field, validator, HttpUrl

class SpendingCategory(str, Enum):
    """Categories for tracking spending patterns."""
    SHOPPING = "shopping"
    GROCERIES = "groceries"
    DINING = "dining"
    TRANSPORT = "transport"
    ENTERTAINMENT = "entertainment"
    BILLS = "bills"
    TRAVEL = "travel"
    PETROL = "petrol"
    OTHER = "other"

class CardType(str, Enum):
    """Types of credit/debit cards."""
    CREDIT = "credit"
    DEBIT = "debit"
    PREPAID = "prepaid"
    CHARGE = "charge"
    BUSINESS = "business"

class CardBenefit(BaseModel):
    """Benefits offered by a card."""
    type: str  # e.g., 'cashback', 'rewards', 'discount'
    value: str  # e.g., '5%', '10x points'
    description: str
    category: Optional[SpendingCategory] = None

class RecommendedCard(BaseModel):
    """Credit/debit card recommendation."""
    id: str
    name: str
    issuer: str  # e.g., 'HDFC', 'ICICI', 'SBI'
    card_type: CardType
    annual_fee: float
    joining_fee: float
    benefits: List[CardBenefit]
    min_income_requirement: Optional[float] = None
    credit_score_requirement: Optional[int] = None
    image_url: Optional[HttpUrl] = None
    apply_url: Optional[HttpUrl] = None
    recommended_for: List[SpendingCategory]
    recommendation_reason: str

class SpendingPattern(BaseModel):
    """Analysis of user's spending in a category."""
    category: SpendingCategory
    amount: float
    percentage: float  # Percentage of total spending
    monthly_average: float
    trend: Literal["increasing", "decreasing", "stable"]
    comparison_to_peers: Literal["lower", "average", "higher"]
    insights: List[str]
    potential_savings: Optional[float] = None

class FinancialGoal(BaseModel):
    """Financial goal model."""
    id: str
    name: str
    target_amount: float
    current_amount: float = 0
    target_date: date
    priority: Literal["low", "medium", "high"] = "medium"
    
    @validator('target_date', pre=True)
    def parse_date(cls, v):
        if isinstance(v, str):
            return datetime.strptime(v, '%Y-%m-%d').date()
        return v

class FinancialProduct(BaseModel):
    """Financial product model."""
    id: str
    name: str
    type: Literal["savings", "investment", "loan", "credit_card", "debit_card", "insurance"]
    description: str
    risk_level: Literal["low", "medium", "high"]
    expected_return: Optional[float] = None
    fees: Optional[float] = None
    minimum_investment: Optional[float] = None
    recommended_for: Optional[List[SpendingCategory]] = None
    recommendation_score: Optional[float] = Field(None, ge=0, le=1)

class RecommendationItem(BaseModel):
    """Single recommendation item."""
    type: Literal[
        "savings", 
        "investment", 
        "debt_management", 
        "budgeting",
        "credit_card",
        "spending_optimization"
    ]
    title: str
    description: str
    priority: Literal["low", "medium", "high"]
    confidence: float = Field(..., ge=0, le=1)
    expected_impact: Optional[str] = None
    related_products: Optional[List[Union[FinancialProduct, RecommendedCard]]] = None
    action_items: Optional[List[str]] = None
    category: Optional[SpendingCategory] = None
    potential_savings: Optional[float] = None

class TransactionData(BaseModel):
    """Transaction data for analysis."""
    amount: float
    category: SpendingCategory
    date: date
    merchant: str
    
    @validator('date', pre=True)
    def parse_date(cls, v):
        if isinstance(v, str):
            return datetime.strptime(v, '%Y-%m-%d').date()
        return v

class CustomerProfile(BaseModel):
    """Customer financial profile."""
    monthly_income: float
    credit_score: Optional[int] = None
    existing_credit_cards: List[str] = []
    preferred_brands: List[str] = []
    preferred_categories: List[SpendingCategory] = []

class RecommendationRequest(BaseModel):
    """Request model for generating recommendations."""
    customer_id: str
    goals: List[FinancialGoal]
    transactions: List[TransactionData]
    customer_profile: CustomerProfile
    risk_tolerance: Literal["conservative", "moderate", "aggressive"] = "moderate"
    time_horizon: Literal["1y", "3y", "5y", "10y"] = "5y"
    include_products: bool = True

class SpendingAnalysis(BaseModel):
    """Analysis of customer's spending patterns."""
    total_spending: float
    spending_by_category: Dict[SpendingCategory, float]
    monthly_average: float
    highest_spending_category: SpendingCategory
    spending_trends: List[SpendingPattern]
    insights: List[str]

class RecommendationResponse(BaseModel):
    """Response model for recommendations with spending analysis."""
    customer_id: str
    generated_at: datetime
    time_horizon: str
    risk_tolerance: str
    spending_analysis: SpendingAnalysis
    recommendations: List[RecommendationItem]
    recommended_cards: List[RecommendedCard]
    summary: str
    next_review_date: date
