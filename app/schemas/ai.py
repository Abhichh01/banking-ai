"""
AI, ML, and fraud detection related Pydantic schemas.
"""
from datetime import datetime, date, timedelta
from decimal import Decimal
from enum import Enum
from typing import Optional, List, Dict, Any, Union, Literal
from pydantic import BaseModel, Field, field_validator, model_validator, HttpUrl, condecimal

from app.models.ai_models import BehavioralPatternType, RecommendationStatus, RecommendationType

from .base import BaseSchema, TimestampMixin, IDSchemaMixin, PaginationSchema

# Enums
class AIServiceType(str, Enum):
    FRAUD_DETECTION = "fraud_detection"
    RECOMMENDATION = "recommendation"
    CHATBOT = "chatbot"
    RISK_ASSESSMENT = "risk_assessment"
    CREDIT_SCORING = "credit_scoring"
    BEHAVIOR_ANALYSIS = "behavior_analysis"
    SENTIMENT_ANALYSIS = "sentiment_analysis"
    DOCUMENT_ANALYSIS = "document_analysis"
    VOICE_ASSISTANT = "voice_assistant"
    PREDICTIVE_ANALYTICS = "predictive_analytics"

class AIProvider(str, Enum):
    OPENAI = "openai"
    AZURE_AI = "azure_ai"
    AWS_BEDROCK = "aws_bedrock"
    GOOGLE_AI = "google_ai"
    ANTHROPIC = "anthropic"
    HUGGINGFACE = "huggingface"
    CUSTOM = "custom"

class AIServiceStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    MAINTENANCE = "maintenance"
    ERROR = "error"

class FraudType(str, Enum):
    CARD_FRAUD = "card_fraud"
    ACCOUNT_TAKEOVER = "account_takeover"
    MONEY_LAUNDERING = "money_laundering"
    IDENTITY_THEFT = "identity_theft"
    PHISHING = "phishing"
    PAYMENT_FRAUD = "payment_fraud"
    LOAN_FRAUD = "loan_fraud"
    INSURANCE_FRAUD = "insurance_fraud"
    FIRST_PARTY_FRAUD = "first_party_fraud"
    SYNTHETIC_IDENTITY = "synthetic_identity"
    OTHER = "other"

class AlertStatus(str, Enum):
    OPEN = "open"
    IN_REVIEW = "in_review"
    RESOLVED = "resolved"
    FALSE_POSITIVE = "false_positive"
    ESCALATED = "escalated"
    CLOSED = "closed"

class AlertSeverity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"

# AI Service schemas
class AIServiceBase(BaseModel):
    name: str = Field(..., max_length=100)
    service_type: AIServiceType
    provider: AIProvider
    status: AIServiceStatus = AIServiceStatus.ACTIVE
    endpoint: Optional[HttpUrl] = None
    api_key: Optional[str] = Field(None, max_length=255)
    model_name: Optional[str] = Field(None, max_length=100)
    version: str = "1.0.0"
    is_active: bool = True
    metadata: Optional[Dict[str, Any]] = None

class AIServiceCreate(AIServiceBase):
    pass

class AIServiceUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    status: Optional[AIServiceStatus] = None
    endpoint: Optional[HttpUrl] = None
    api_key: Optional[str] = Field(None, max_length=255)
    model_name: Optional[str] = Field(None, max_length=100)
    version: Optional[str] = None
    is_active: Optional[bool] = None
    metadata: Optional[Dict[str, Any]] = None

class AIServiceInDBBase(AIServiceBase, IDSchemaMixin, TimestampMixin):
    model_config = {
        "from_attributes": True
    }

class AIService(AIServiceInDBBase):
    pass

# Fraud Alert schemas
class FraudAlertBase(BaseModel):
    """Base model for fraud detection alerts.
    
    Represents potential fraudulent activities detected by the AI system,
    including transaction anomalies, account takeovers, and other suspicious patterns.
    """
    alert_type: str = Field(
        ...,
        max_length=100,
        description="Type/category of the fraud alert"
    )
    description: str = Field(
        ...,
        description="Detailed description of the alert"
    )
    severity: str = Field(
        "medium",
        description="Severity level of the alert"
    )
    status: str = Field(
        "open",
        description="Current status of the alert"
    )
    confidence_score: float = Field(
        0.0,
        ge=0.0,
        le=1.0,
        description="AI model's confidence in this alert (0-1)"
    )
    transaction_id: Optional[int] = Field(
        None,
        description="ID of the related transaction, if applicable"
    )
    user_id: int = Field(
        ...,
        description="ID of the user this alert is associated with"
    )
    account_id: Optional[int] = Field(
        None,
        description="ID of the specific account, if applicable"
    )
    metadata_: Dict[str, Any] = Field(
        default_factory=dict,
        alias="metadata",
        description="Additional metadata about the alert"
    )
    detected_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="When the alert was first detected"
    )
    
    class Config:
        validate_by_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }
        json_schema_extra = {
            "example": {
                "alert_type": "unusual_transaction",
                "description": "Unusually large transaction detected compared to spending patterns",
                "severity": "high",
                "status": "open",
                "confidence_score": 0.92,
                "user_id": 12345,
                "account_id": 67890,
                "metadata": {
                    "transaction_amount": 2499.99,
                    "avg_previous_transaction": 125.50,
                    "location_mismatch": True,
                    "device_trust_score": 0.65
                },
                "detected_at": "2023-06-15T14:30:00Z"
            }
        }

class FraudAlertCreate(FraudAlertBase):
    """Schema for creating a new fraud alert.
    
    Extends the base schema with validation specific to new alerts.
    """
    @field_validator('alert_type')
    def validate_alert_type(cls, v):
        """Validate that alert type is one of the allowed values."""
        allowed_types = [t.value for t in FraudType]
        if v not in allowed_types:
            raise ValueError(f"Alert type must be one of: {', '.join(allowed_types)}")
        return v
    
    @field_validator('severity')
    def validate_initial_severity(cls, v):
        """Ensure severity is one of the allowed values."""
        if v not in [s.value for s in AlertSeverity]:
            raise ValueError(f"Severity must be one of: {', '.join([s.value for s in AlertSeverity])}")
        return v
    
    @field_validator('status')
    def validate_initial_status(cls, v):
        """Ensure new alerts start with a valid initial status."""
        if v != 'open':
            raise ValueError("New alerts must be created with status 'open'")
        return v
    
    class Config(FraudAlertBase.Config):
        json_schema_extra = {
            "example": {
                **FraudAlertBase.Config.json_schema_extra["example"],
                "alert_type": "unusual_transaction",
                "status": "open"
            }
        }

class FraudAlertUpdate(BaseModel):
    """Schema for updating an existing fraud alert.
    
    Only allows updating specific fields that should be mutable after creation.
    """
    status: Optional[AlertStatus] = Field(
        None,
        description="Updated status of the alert"
    )
    severity: Optional[AlertSeverity] = Field(
        None,
        description="Updated severity level"
    )
    resolution_notes: Optional[str] = Field(
        None, 
        max_length=1000,
        description="Notes about how the alert was resolved"
    )
    resolved_by: Optional[int] = Field(
        None,
        description="ID of the user who resolved the alert"
    )
    metadata_: Optional[Dict[str, Any]] = Field(
        None,
        alias="metadata",
        description="Metadata to merge with existing metadata"
    )
    confidence_score: Optional[float] = Field(
        None,
        ge=0.0,
        le=1.0,
        description="Updated confidence score (0-1)"
    )
    
    @field_validator('status')
    def validate_status_transition(cls, v):
        """Validate status transitions follow allowed workflow."""
        if v is not None and v not in [s.value for s in AlertStatus]:
            raise ValueError(f"Status must be one of: {', '.join([s.value for s in AlertStatus])}")
        return v
    
    @model_validator(mode='after')
    def validate_resolution_fields(self):
        """Validate that resolution fields are provided when resolving an alert."""
        status = self.status
        resolved_by = self.resolved_by
        resolution_notes = self.resolution_notes

        if status in ['resolved', 'false_positive']:
            if not resolved_by:
                raise ValueError("resolved_by is required when resolving an alert")
            if not resolution_notes:
                raise ValueError("resolution_notes are required when resolving an alert")

        return self
    
    class Config:
        validate_by_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }
        json_schema_extra = {
            "example": {
                "status": "resolved",
                "severity": "high",
                "resolution_notes": "Verified with user - this was an expected payment",
                "resolved_by": 1,
                "metadata": {
                    "verification_method": "phone_call",
                    "agent_notes": "Customer confirmed this was an expected payment"
                },
                "confidence_score": 0.95
            }
        }

class FraudAlertInDBBase(FraudAlertBase, IDSchemaMixin, TimestampMixin):
    """Base model for database-persisted fraud alerts.
    
    Includes database-specific fields like IDs and timestamps.
    """
    resolved_at: Optional[datetime] = Field(
        None,
        description="When the alert was resolved"
    )
    resolved_by: Optional[int] = Field(
        None,
        description="ID of the user who resolved the alert"
    )
    resolution_notes: Optional[str] = Field(
        None,
        max_length=1000,
        description="Notes about how the alert was resolved"
    )
    
    class Config(FraudAlertBase.Config):
        from_attributes = True
        json_encoders = {
            **FraudAlertBase.Config.json_encoders,
        }
        json_schema_extra = {
            "example": {
                **FraudAlertBase.Config.json_schema_extra["example"],
                "id": 1,
                "created_at": "2023-06-15T14:30:00Z",
                "updated_at": "2023-06-16T09:15:00Z",
                "resolved_at": None,
                "resolved_by": None,
                "resolution_notes": None
            }
        }

class FraudAlert(FraudAlertInDBBase):
    """Complete fraud alert model with additional computed properties and relationships."""
    
    @property
    def is_resolved(self) -> bool:
        """Check if the alert has been resolved."""
        return self.status in ['resolved', 'false_positive']
    
    @property
    def requires_immediate_attention(self) -> bool:
        """Check if the alert requires immediate attention."""
        return (self.severity in ['high', 'critical'] and 
                self.status == 'open' and 
                self.confidence_score >= 0.8)
    
    @property
    def time_to_resolution(self) -> Optional[timedelta]:
        """Calculate time taken to resolve the alert, if resolved."""
        if not self.is_resolved or not self.resolved_at:
            return None
        return self.resolved_at - self.detected_at
    
    @property
    def risk_level(self) -> str:
        """Calculate overall risk level based on severity and confidence."""
        if self.severity == 'critical' and self.confidence_score >= 0.8:
            return 'extreme'
        elif self.severity in ['high', 'critical'] and self.confidence_score >= 0.6:
            return 'high'
        elif self.severity in ['medium', 'high'] and self.confidence_score >= 0.4:
            return 'medium'
        return 'low'
    
    class Config(FraudAlertInDBBase.Config):
        json_schema_extra = {
            "example": {
                **FraudAlertInDBBase.Config.json_schema_extra["example"],
                "is_resolved": False,
                "requires_immediate_attention": True,
                "time_to_resolution": None,
                "risk_level": "high"
            }
        }

# AI Recommendation schemas
class AIRecommendationBase(BaseModel):
    """Base model for AI-generated recommendations.
    
    Represents personalized financial recommendations generated by AI models
    based on user behavior, transactions, and financial goals.
    """
    title: str = Field(
        ...,
        max_length=255,
        description="Short, descriptive title of the recommendation"
    )
    description: str = Field(
        ...,
        description="Detailed explanation of the recommendation"
    )
    recommendation_type: str = Field(
        ...,
        max_length=100,
        description="Type/category of the recommendation"
    )
    confidence_score: float = Field(
        0.0,
        ge=0.0,
        le=1.0,
        description="AI model's confidence in this recommendation (0-1)"
    )
    status: str = Field(
        "pending",
        description="Current status of the recommendation"
    )
    user_id: Optional[int] = Field(
        None,
        description="ID of the user this recommendation is for"
    )
    account_id: Optional[int] = Field(
        None,
        description="Optional account ID if recommendation is account-specific"
    )
    metadata_: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        alias="metadata",
        description="Additional metadata about the recommendation"
    )
    expires_at: Optional[datetime] = Field(
        None,
        description="When this recommendation expires"
    )
    
    class Config:
        validate_by_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }
        json_schema_extra = {
            "example": {
                "title": "Increase emergency fund",
                "description": "Based on your spending patterns, we recommend...",
                "recommendation_type": "savings_goal",
                "confidence_score": 0.85,
                "status": "pending",
                "user_id": 12345,
                "metadata": {
                    "target_amount": 10000,
                    "timeline_months": 12,
                    "priority": "high"
                },
                "expires_at": "2023-12-31T23:59:59Z"
            }
        }

class AIRecommendationCreate(AIRecommendationBase):
    """Schema for creating a new AI recommendation.
    
    Extends the base schema with validation specific to new recommendations.
    """
    @field_validator('recommendation_type')
    def validate_recommendation_type(cls, v):
        """Validate that recommendation type is one of the allowed values."""
        allowed_types = [t.value for t in RecommendationType]
        if v not in allowed_types:
            raise ValueError(f"Recommendation type must be one of: {', '.join(allowed_types)}")
        return v
    
    @field_validator('status')
    def validate_initial_status(cls, v):
        """Ensure new recommendations start with a valid initial status."""
        valid_initial = ['pending', 'active']
        if v not in valid_initial:
            raise ValueError(f"New recommendations must have status one of: {', '.join(valid_initial)}")
        return v
    
    class Config(AIRecommendationBase.Config):
        json_schema_extra = {
            "example": {
                **AIRecommendationBase.Config.json_schema_extra["example"],
                "status": "pending"
            }
        }

class AIRecommendationUpdate(BaseModel):
    """Schema for updating an existing AI recommendation.
    
    Only allows updating specific fields that should be mutable after creation.
    """
    status: Optional[str] = Field(
        None,
        description="Updated status of the recommendation"
    )
    confidence_score: Optional[float] = Field(
        None, 
        ge=0.0, 
        le=1.0,
        description="Updated confidence score (0-1)"
    )
    metadata_: Optional[Dict[str, Any]] = Field(
        None,
        alias="metadata",
        description="Metadata to merge with existing metadata"
    )
    expires_at: Optional[datetime] = Field(
        None,
        description="New expiration datetime for the recommendation"
    )
    user_feedback: Optional[str] = Field(
        None,
        max_length=1000,
        description="Optional user feedback on the recommendation"
    )
    feedback_rating: Optional[int] = Field(
        None,
        ge=1,
        le=5,
        description="User rating (1-5) for the recommendation"
    )
    
    @field_validator('status')
    def validate_status_transition(cls, v, values, **kwargs):
        """Validate status transitions follow allowed workflow."""
        if v not in [s.value for s in RecommendationStatus]:
            raise ValueError(f"Status must be one of: {', '.join([s.value for s in RecommendationStatus])}")
        return v
    
    class Config:
        validate_by_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }
        json_schema_extra = {
            "example": {
                "status": "accepted",
                "user_feedback": "This was very helpful!",
                "feedback_rating": 5,
                "metadata": {
                    "action_taken": "setup_auto_savings",
                    "notes": "User set up automatic transfers to savings"
                }
            }
        }

class AIRecommendationInDBBase(AIRecommendationBase, IDSchemaMixin, TimestampMixin):
    """Base model for database-persisted AI recommendations.
    
    Includes database-specific fields like IDs and timestamps.
    """
    class Config(AIRecommendationBase.Config):
        from_attributes = True
        json_encoders = {
            **AIRecommendationBase.Config.json_encoders,
        }
        json_schema_extra = {
            "example": {
                **AIRecommendationBase.Config.json_schema_extra["example"],
                "id": 1,
                "created_at": "2023-06-15T14:30:00Z",
                "updated_at": "2023-06-16T09:15:00Z"
            }
        }

class AIRecommendation(AIRecommendationInDBBase):
    """Complete AI recommendation model with additional computed properties."""
    
    @property
    def is_expired(self) -> bool:
        """Check if the recommendation has expired."""
        if not self.expires_at:
            return False
        return datetime.utcnow() > self.expires_at
    
    @property
    def is_actionable(self) -> bool:
        """Check if the recommendation can still be acted upon."""
        return self.status in ['pending', 'active'] and not self.is_expired
    
    @property
    def priority_level(self) -> str:
        """Get a human-readable priority level based on confidence score."""
        if self.confidence_score >= 0.9:
            return "critical"
        elif self.confidence_score >= 0.7:
            return "high"
        elif self.confidence_score >= 0.5:
            return "medium"
        return "low"
    
    class Config(AIRecommendationInDBBase.Config):
        json_schema_extra = {
            "example": {
                **AIRecommendationInDBBase.Config.json_schema_extra["example"],
                "is_expired": False,
                "is_actionable": True,
                "priority_level": "high"
            }
        }

# Behavioral Pattern schemas
class BehavioralPatternBase(BaseModel):
    """Base model for behavioral pattern analysis.
    
    Represents AI-identified patterns in user behavior, such as spending habits,
    transaction timing, and other financial behaviors.
    """
    pattern_type: str = Field(
        ...,
        max_length=100,
        description="Type of behavioral pattern identified"
    )
    description: Optional[str] = Field(
        None,
        description="Human-readable description of the pattern"
    )
    confidence_score: float = Field(
        0.0, 
        ge=0.0, 
        le=1.0,
        description="Confidence score of the pattern detection (0-1)"
    )
    user_id: int = Field(
        ...,
        description="ID of the user this pattern belongs to"
    )
    account_id: Optional[int] = Field(
        None,
        description="Optional account ID if pattern is account-specific"
    )
    metadata_: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        alias="metadata",
        description="Additional metadata about the pattern"
    )
    detected_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="When this pattern was first detected"
    )
    is_active: bool = Field(
        True,
        description="Whether this pattern is currently active"
    )
    
    class Config:
        validate_by_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }
        json_schema_extra = {
            "example": {
                "pattern_type": "spending_habit",
                "description": "Monthly subscription spending pattern detected",
                "confidence_score": 0.87,
                "user_id": 12345,
                "metadata": {
                    "category": "subscriptions",
                    "monthly_amount": 49.99,
                    "services": ["streaming", "software"]
                }
            }
        }

class BehavioralPatternCreate(BehavioralPatternBase):
    """Schema for creating a new behavioral pattern record."""
    
    @field_validator('pattern_type')
    def validate_pattern_type(cls, v):
        """Validate that pattern type is one of the allowed values."""
        allowed_types = [t.value for t in BehavioralPatternType]
        if v not in allowed_types:
            raise ValueError(f"Pattern type must be one of: {', '.join(allowed_types)}")
        return v
    
    class Config(BehavioralPatternBase.Config):
        json_schema_extra = {
            "example": {
                **BehavioralPatternBase.Config.json_schema_extra["example"],
                "detected_at": "2023-06-15T14:30:00Z"
            }
        }

class BehavioralPatternUpdate(BaseModel):
    """Schema for updating an existing behavioral pattern."""
    confidence_score: Optional[float] = Field(
        None, 
        ge=0.0, 
        le=1.0,
        description="Updated confidence score"
    )
    is_active: Optional[bool] = Field(
        None,
        description="Set to false to deactivate this pattern"
    )
    metadata_: Optional[Dict[str, Any]] = Field(
        None,
        alias="metadata",
        description="Metadata to merge with existing metadata"
    )
    
    class Config:
        validate_by_name = True
        json_schema_extra = {
            "example": {
                "confidence_score": 0.92,
                "is_active": True,
                "metadata": {
                    "verified_by": "analyst_john",
                    "review_notes": "Confirmed pattern through manual review"
                }
            }
        }

class BehavioralPatternInDBBase(BehavioralPatternBase, IDSchemaMixin, TimestampMixin):
    """Base model for database-persisted behavioral patterns."""
    
    class Config(BehavioralPatternBase.Config):
        from_attributes = True
        json_encoders = {
            **BehavioralPatternBase.Config.json_encoders,
        }
        json_schema_extra = {
            "example": {
                **BehavioralPatternBase.Config.json_schema_extra["example"],
                "id": 1,
                "created_at": "2023-06-15T14:30:00Z",
                "updated_at": "2023-06-16T09:15:00Z"
            }
        }

class BehavioralPattern(BehavioralPatternInDBBase):
    """Full behavioral pattern model with additional computed properties."""
    
    @property
    def is_high_confidence(self) -> bool:
        """Check if the pattern has high confidence."""
        return self.confidence_score >= 0.8
    
    @property
    def is_recent(self) -> bool:
        """Check if the pattern was detected recently (last 30 days)."""
        return (datetime.utcnow() - self.detected_at).days <= 30
    
    class Config(BehavioralPatternInDBBase.Config):
        json_schema_extra = {
            "example": {
                **BehavioralPatternInDBBase.Config.json_schema_extra["example"],
                "is_high_confidence": True,
                "is_recent": True
            }
        }

# Model Training schemas
class ModelTrainingBase(BaseModel):
    model_name: str = Field(..., max_length=100)
    model_version: str = Field(..., max_length=50)
    training_data_start_date: date
    training_data_end_date: date
    metrics: Dict[str, Any]
    training_parameters: Dict[str, Any]
    training_status: str = Field(..., max_length=50)  # running, completed, failed
    trained_by: Optional[str] = None
    notes: Optional[str] = None

class ModelTrainingCreate(ModelTrainingBase):
    pass

class ModelTrainingUpdate(BaseModel):
    training_status: Optional[str] = None
    metrics: Optional[Dict[str, Any]] = None
    notes: Optional[str] = None

class ModelTrainingInDBBase(ModelTrainingBase, IDSchemaMixin, TimestampMixin):
    class Config:
        from_attributes = True

class ModelTraining(ModelTrainingInDBBase):
    pass

# Response models
class AIServiceResponse(BaseModel):
    success: bool = True
    data: AIService

class AIServiceListResponse(BaseModel):
    success: bool = True
    data: List[AIService]
    total: int
    page: int
    page_size: int

class FraudAlertResponse(BaseModel):
    success: bool = True
    data: FraudAlert

class FraudAlertListResponse(BaseModel):
    success: bool = True
    data: List[FraudAlert]
    total: int
    page: int
    page_size: int

class AIRecommendationResponse(BaseModel):
    success: bool = True
    data: AIRecommendation

class AIRecommendationListResponse(BaseModel):
    success: bool = True
    data: List[AIRecommendation]
    total: int
    page: int
    page_size: int

class BehavioralPatternResponse(BaseModel):
    success: bool = True
    data: BehavioralPattern

class BehavioralPatternListResponse(BaseModel):
    success: bool = True
    data: List[BehavioralPattern]
    total: int
    page: int
    page_size: int

class ModelTrainingResponse(BaseModel):
    success: bool = True
    data: ModelTraining

class ModelTrainingListResponse(BaseModel):
    success: bool = True
    data: List[ModelTraining]
    total: int

# Query parameters
class FraudAlertFilter(PaginationSchema):
    """Filter criteria for querying fraud alerts.
    
    Supports filtering by various alert attributes, time ranges, and confidence scores.
    """
    alert_type: Optional[Union[FraudType, List[FraudType]]] = Field(
        None,
        description="Filter by one or more alert types"
    )
    status: Optional[Union[AlertStatus, List[AlertStatus]]] = Field(
        None,
        description="Filter by one or more status values"
    )
    severity: Optional[Union[AlertSeverity, List[AlertSeverity]]] = Field(
        None,
        description="Filter by one or more severity levels"
    )
    min_confidence: Optional[float] = Field(
        None,
        ge=0.0,
        le=1.0,
        description="Minimum confidence score (0-1)"
    )
    max_confidence: Optional[float] = Field(
        None,
        ge=0.0,
        le=1.0,
        description="Maximum confidence score (0-1)"
    )
    user_id: Optional[Union[int, List[int]]] = Field(
        None,
        description="Filter by one or more user IDs"
    )
    account_id: Optional[Union[int, List[int], Literal["null"]]] = Field(
        None,
        description="Filter by one or more account IDs or 'null' for account-agnostic alerts"
    )
    transaction_id: Optional[Union[int, List[int]]] = Field(
        None,
        description="Filter by one or more transaction IDs"
    )
    min_detected_date: Optional[datetime] = Field(
        None,
        description="Earliest detection date to include"
    )
    max_detected_date: Optional[datetime] = Field(
        None,
        description="Latest detection date to include"
    )
    resolved: Optional[bool] = Field(
        None,
        description="Filter by resolution status"
    )
    min_resolution_time_minutes: Optional[int] = Field(
        None,
        ge=0,
        description="Minimum time to resolution in minutes (filters resolved alerts)"
    )
    max_resolution_time_minutes: Optional[int] = Field(
        None,
        ge=0,
        description="Maximum time to resolution in minutes (filters resolved alerts)"
    )
    risk_level: Optional[Union[str, List[str]]] = Field(
        None,
        description="Filter by risk level (extreme/high/medium/low)"
    )
    
    @field_validator('alert_type', 'status', 'severity', 'user_id', 'account_id', 'transaction_id', 'risk_level')
    def convert_single_to_list(cls, v, info):
        """Convert single values to single-item lists for consistent filtering."""
        if v is None:
            return None
        if isinstance(v, (list, set)):
            return list(v)
        return [v]
    
    @field_validator('risk_level')
    def validate_risk_level(cls, v):
        """Validate risk level values."""
        if v is None:
            return None
        
        valid_levels = ['extreme', 'high', 'medium', 'low']
        invalid = [level for level in v if level not in valid_levels]
        if invalid:
            raise ValueError(f"Invalid risk level(s): {', '.join(invalid)}. Must be one of: {', '.join(valid_levels)}")
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "alert_type": ["unusual_transaction", "account_takeover"],
                "status": ["open", "investigating"],
                "severity": ["high", "critical"],
                "min_confidence": 0.7,
                "resolved": False,
                "min_detected_date": "2023-01-01T00:00:00Z",
                "risk_level": ["high", "extreme"],
                "page": 1,
                "page_size": 20
            }
        }

class AIRecommendationFilter(PaginationSchema):
    """Filter criteria for querying AI recommendations."""
    
    recommendation_type: Optional[str] = Field(
        None,
        description="Filter by specific recommendation type"
    )
    status: Optional[str] = Field(
        None,
        description="Filter by recommendation status"
    )
    min_confidence: Optional[float] = Field(
        None,
        ge=0.0,
        le=1.0,
        description="Minimum confidence score (0-1)"
    )
    max_confidence: Optional[float] = Field(
        None,
        ge=0.0,
        le=1.0,
        description="Maximum confidence score (0-1)"
    )
    user_id: Optional[int] = Field(
        None,
        description="Filter by specific user ID"
    )
    account_id: Optional[Union[int, Literal["null"]]] = Field(
        None,
        description="Filter by specific account ID or 'null' for account-agnostic recommendations"
    )
    expired: Optional[bool] = Field(
        None,
        description="Filter by expiration status"
    )
    min_created_date: Optional[date] = Field(
        None,
        description="Earliest creation date to include"
    )
    max_created_date: Optional[date] = Field(
        None,
        description="Latest creation date to include"
    )
    priority: Optional[str] = Field(
        None,
        description="Filter by priority level (critical/high/medium/low)"
    )
    has_feedback: Optional[bool] = Field(
        None,
        description="Filter by whether feedback has been provided"
    )
    
    @field_validator('status')
    def validate_status(cls, v):
        """Validate status against allowed values if provided."""
        if v is not None and v not in [s.value for s in RecommendationStatus]:
            raise ValueError(f"Status must be one of: {', '.join([s.value for s in RecommendationStatus])}")
        return v
    
    @field_validator('priority')
    def validate_priority(cls, v):
        """Validate priority level if provided."""
        if v is not None and v not in ["critical", "high", "medium", "low"]:
            raise ValueError("Priority must be one of: critical, high, medium, low")
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "recommendation_type": "savings_goal",
                "status": "pending",
                "min_confidence": 0.7,
                "priority": "high",
                "has_feedback": False,
                "page": 1,
                "page_size": 20
            }
        }

class BehavioralPatternFilter(PaginationSchema):
    """Filter criteria for querying behavioral patterns."""
    
    pattern_type: Optional[str] = Field(
        None,
        description="Filter by specific pattern type"
    )
    is_active: Optional[bool] = Field(
        None,
        description="Filter by active/inactive status"
    )
    min_confidence: Optional[float] = Field(
        None, 
        ge=0.0, 
        le=1.0,
        description="Minimum confidence score (0-1)"
    )
    max_confidence: Optional[float] = Field(
        None, 
        ge=0.0, 
        le=1.0,
        description="Maximum confidence score (0-1)"
    )
    user_id: Optional[int] = Field(
        None,
        description="Filter by specific user ID"
    )
    account_id: Optional[int] = Field(
        None,
        description="Filter by specific account ID"
    )
    start_date: Optional[date] = Field(
        None,
        description="Earliest detection date to include"
    )
    end_date: Optional[date] = Field(
        None,
        description="Latest detection date to include"
    )
    min_detection_age_days: Optional[int] = Field(
        None,
        ge=0,
        description="Minimum age of detection in days"
    )
    max_detection_age_days: Optional[int] = Field(
        None,
        ge=0,
        description="Maximum age of detection in days"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "pattern_type": "spending_habit",
                "min_confidence": 0.7,
                "is_active": True,
                "start_date": "2023-01-01",
                "end_date": "2023-12-31",
                "page": 1,
                "page_size": 20
            }
        }

# AI Service Health Check
class AIServiceHealth(BaseModel):
    service_id: int
    service_name: str
    status: str
    response_time_ms: Optional[float] = None
    last_checked: datetime
    error: Optional[str] = None
    metrics: Optional[Dict[str, Any]] = None

# AI Model Prediction Request/Response
class AIModelPredictionRequest(BaseModel):
    model_name: str
    model_version: str
    input_data: Dict[str, Any]
    request_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class AIModelPredictionResponse(BaseModel):
    success: bool = True
    request_id: str
    model_name: str
    model_version: str
    prediction: Any
    confidence: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None
    processing_time_ms: Optional[float] = None
