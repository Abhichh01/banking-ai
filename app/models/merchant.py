"""
Merchant model for managing merchant information and categories.
"""
from datetime import datetime
from typing import Optional, Dict, Any, List
from sqlalchemy import Column, Integer, String, Text, JSON, ForeignKey, DateTime, Float, Enum, Index
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import ENUM as PgEnum, JSONB
from sqlalchemy.sql import func

from .base import ModelBase

class MerchantCategory(str, Enum):
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

class MerchantStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    UNDER_REVIEW = "under_review"

class Merchant(ModelBase):
    """
    Merchant model representing businesses where transactions occur.
    """
    __tablename__ = 'merchants'
    
    merchant_id = Column(String(100), primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    category = Column(Enum(MerchantCategory), nullable=False)
    mcc_code = Column(String(10), index=True)  # Merchant Category Code
    description = Column(Text, nullable=True)
    website = Column(String(255), nullable=True)
    phone = Column(String(20), nullable=True)
    email = Column(String(100), nullable=True)
    
    # Location Information
    address_line1 = Column(String(200), nullable=True)
    address_line2 = Column(String(200), nullable=True)
    city = Column(String(100), nullable=True)
    state = Column(String(100), nullable=True)
    postal_code = Column(String(20), nullable=True)
    country = Column(String(100), default="India")
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    
    # Business Information
    business_type = Column(String(100), nullable=True)
    business_registration_number = Column(String(100), nullable=True)
    tax_id = Column(String(100), nullable=True)
    
    # Risk and Compliance
    risk_score = Column(Float, default=0.0)  # 0-1 scale
    status = Column(Enum(MerchantStatus), default=MerchantStatus.ACTIVE)
    is_high_risk = Column(Boolean, default=False)
    last_reviewed = Column(DateTime, nullable=True)
    
    # Metadata and Timestamps
    metadata_ = Column('metadata', JSONB, default=dict)  # For additional attributes
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    transactions = relationship("Transaction", back_populates="merchant")
    
    # Indexes
    __table_args__ = (
        Index('idx_merchant_name', 'name'),
        Index('idx_merchant_category', 'category'),
        Index('idx_merchant_risk', 'risk_score'),
        Index('idx_merchant_status', 'status'),
        Index('idx_merchant_mcc', 'mcc_code'),
        {'extend_existing': True}
    )
    
    def __repr__(self) -> str:
        return f"<Merchant {self.name} ({self.merchant_id})>"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary."""
        return {
            'merchant_id': self.merchant_id,
            'name': self.name,
            'category': self.category.value if self.category else None,
            'mcc_code': self.mcc_code,
            'description': self.description,
            'website': self.website,
            'phone': self.phone,
            'email': self.email,
            'address': {
                'line1': self.address_line1,
                'line2': self.address_line2,
                'city': self.city,
                'state': self.state,
                'postal_code': self.postal_code,
                'country': self.country,
                'coordinates': {
                    'latitude': self.latitude,
                    'longitude': self.longitude
                } if self.latitude and self.longitude else None
            },
            'business_info': {
                'type': self.business_type,
                'registration_number': self.business_registration_number,
                'tax_id': self.tax_id
            },
            'risk': {
                'score': self.risk_score,
                'status': self.status.value if self.status else None,
                'is_high_risk': self.is_high_risk,
                'last_reviewed': self.last_reviewed.isoformat() if self.last_reviewed else None
            },
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
