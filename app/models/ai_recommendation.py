"""
AI Recommendation model for personalized banking recommendations.
"""
from datetime import date, datetime
from enum import Enum
from typing import Dict, Any, List, Optional
from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Date, Float, Enum as SQLEnum, Index
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func

from .base import ModelBase

class RecommendationType(str, Enum):
    PRODUCT = "product"
    SERVICE = "service"
    FEATURE = "feature"
    BEHAVIORAL_CHANGE = "behavioral_change"
    RISK_MITIGATION = "risk_mitigation"
    SAVINGS_OPPORTUNITY = "savings_opportunity"
    INVESTMENT = "investment"
    LOAN = "loan"
    INSURANCE = "insurance"
    CARD_UPGRADE = "card_upgrade"
    ACCOUNT_UPGRADE = "account_upgrade"

class RecommendationStatus(str, Enum):
    ACTIVE = "active"
    ACCEPTED = "accepted"
    DECLINED = "declined"
    EXPIRED = "expired"
    IMPLEMENTED = "implemented"
    PENDING = "pending"
    IN_REVIEW = "in_review"

class RecommendationPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class AIRecommendation(ModelBase):
    """
    Model for storing AI-generated recommendations for users.
    """
    __tablename__ = 'ai_recommendations'
    
    recommendation_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Recommendation details
    recommendation_type = Column(SQLEnum(RecommendationType), nullable=False, index=True)
    product_category = Column(String(100), index=True, nullable=True)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    reasoning = Column(Text)  # AI explanation for the recommendation
    
    # Recommendation metrics
    confidence_score = Column(Float, nullable=False)  # 0-1 scale
    priority = Column(SQLEnum(RecommendationPriority), default=RecommendationPriority.MEDIUM)
    estimated_benefit = Column(Text)  # Expected benefit in natural language
    estimated_monetary_value = Column(Float, nullable=True)  # Estimated monetary value if applicable
    
    # User interaction
    call_to_action = Column(String(200))
    status = Column(SQLEnum(RecommendationStatus), default=RecommendationStatus.ACTIVE)
    user_feedback = Column(Text)
    feedback_rating = Column(Integer)  # 1-5 scale
    feedback_timestamp = Column(DateTime(timezone=True), nullable=True)
    
    # Expiration and timing
    expiry_date = Column(Date, index=True, nullable=True)
    implemented_date = Column(DateTime(timezone=True), nullable=True)
    
    # AI metadata
    ai_model_version = Column(String(50))
    source_pattern_id = Column(Integer, ForeignKey('behavioral_patterns.pattern_id'), nullable=True)
    
    # Metadata and timestamps
    metadata_ = Column('metadata', JSONB, default=dict)  # For additional attributes
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="ai_recommendations")
    source_pattern = relationship("BehavioralPattern", back_populates="generated_recommendations")
    
    # Indexes
    __table_args__ = (
        Index('idx_recommendation_user_status', 'user_id', 'status'),
        Index('idx_recommendation_type', 'recommendation_type'),
        Index('idx_confidence_score', 'confidence_score'),
        Index('idx_expiry_date', 'expiry_date'),
        Index('idx_priority', 'priority'),
        {'extend_existing': True}
    )
    
    def __repr__(self) -> str:
        return f"<AIRecommendation {self.title} (ID: {self.recommendation_id})>"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary."""
        return {
            'recommendation_id': self.recommendation_id,
            'user_id': self.user_id,
            'type': self.recommendation_type.value if self.recommendation_type else None,
            'product_category': self.product_category,
            'title': self.title,
            'description': self.description,
            'reasoning': self.reasoning,
            'metrics': {
                'confidence_score': self.confidence_score,
                'priority': self.priority.value if self.priority else None,
                'estimated_benefit': self.estimated_benefit,
                'estimated_monetary_value': self.estimated_monetary_value
            },
            'user_interaction': {
                'call_to_action': self.call_to_action,
                'status': self.status.value if self.status else None,
                'user_feedback': self.user_feedback,
                'feedback_rating': self.feedback_rating,
                'feedback_timestamp': self.feedback_timestamp.isoformat() if self.feedback_timestamp else None
            },
            'timing': {
                'expiry_date': self.expiry_date.isoformat() if self.expiry_date else None,
                'implemented_date': self.implemented_date.isoformat() if self.implemented_date else None,
                'created_at': self.created_at.isoformat() if self.created_at else None,
                'updated_at': self.updated_at.isoformat() if self.updated_at else None
            },
            'ai_metadata': {
                'model_version': self.ai_model_version,
                'source_pattern_id': self.source_pattern_id
            },
            'metadata': self.metadata_
        }
    
    def is_active(self) -> bool:
        """Check if the recommendation is still active and not expired."""
        if self.status in [RecommendationStatus.ACCEPTED, RecommendationStatus.DECLINED, RecommendationStatus.IMPLEMENTED]:
            return False
        
        if self.expiry_date and date.today() > self.expiry_date:
            return False
            
        return True
    
    def mark_accepted(self, feedback: Optional[str] = None, rating: Optional[int] = None):
        """Mark the recommendation as accepted by the user."""
        self.status = RecommendationStatus.ACCEPTED
        self.user_feedback = feedback
        self.feedback_rating = rating
        self.feedback_timestamp = func.now()
    
    def mark_declined(self, feedback: Optional[str] = None, rating: Optional[int] = None):
        """Mark the recommendation as declined by the user."""
        self.status = RecommendationStatus.DECLINED
        self.user_feedback = feedback
        self.feedback_rating = rating
        self.feedback_timestamp = func.now()
    
    def mark_implemented(self, implementation_notes: Optional[str] = None):
        """Mark the recommendation as implemented."""
        self.status = RecommendationStatus.IMPLEMENTED
        self.implemented_date = func.now()
        if implementation_notes:
            self.metadata_ = {**self.metadata_, 'implementation_notes': implementation_notes}
