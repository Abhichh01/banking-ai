"""
User model for authentication and profile management.
"""
from datetime import datetime, date, timezone
from enum import Enum
from typing import Dict, List, Optional, Any, Union
from uuid import uuid4

from sqlalchemy import (
    Boolean, 
    Column, 
    DateTime, 
    Date as SQLDate,
    ForeignKey, 
    Integer, 
    String, 
    Text,
    Float,
    Enum as SQLEnum,
    Index,
    Numeric,
    CheckConstraint,
    func,
    text,
    Table
)
from sqlalchemy.orm import relationship, Mapped

# Import database-agnostic types
from app.db.types import JSON, UUID, Interval

from .base import ModelBase


class UserRole(str, Enum):
    """User roles for access control."""
    CUSTOMER = "customer"
    AGENT = "agent"
    MANAGER = "manager"
    ADMIN = "admin"
    SYSTEM = "system"
    FRAUD_ANALYST = "fraud_analyst"
    CUSTOMER_SERVICE = "customer_service"
    FINANCIAL_ADVISOR = "financial_advisor"


class UserStatus(str, Enum):
    """User account status."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING_VERIFICATION = "pending_verification"
    LOCKED = "locked"
    FRAUD_HOLD = "fraud_hold"
    DECEASED = "deceased"


class CustomerSegment(str, Enum):
    """Customer segmentation for targeted services."""
    RETAIL = "retail"
    PREMIUM = "premium"
    PRIVATE = "private"
    BUSINESS = "business"
    WEALTH = "wealth"
    CORPORATE = "corporate"
    STUDENT = "student"
    SENIOR = "senior"
    YOUNG_ADULT = "young_adult"


class RiskProfile(str, Enum):
    """User's risk profile for investment and credit decisions."""
    CONSERVATIVE = "conservative"
    MODERATE = "moderate"
    BALANCED = "balanced"
    GROWTH = "growth"
    AGGRESSIVE = "aggressive"
    NOT_ASSESSED = "not_assessed"


class KYCStatus(str, Enum):
    """KYC verification status."""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    VERIFIED = "verified"
    PENDING_VERIFICATION = "pending_verification"
    REJECTED = "rejected"
    EXPIRED = "expired"


class User(ModelBase):
    """User account model with authentication and profile data.
    
    This model represents a user in the banking system with comprehensive
    authentication, profile, and relationship data. It serves as the central
    entity linking to all user-related information.
    """
    
    __tablename__ = "users"
    
    # Authentication & Identification
    id = Column(
        UUID,
        primary_key=True,
        default=uuid4,
        index=True,
        unique=True,
        nullable=False,
        comment='Unique identifier for the user'
    )
    email = Column(String(255), unique=True, nullable=False, index=True,
                 comment='Primary email address for communication')
    phone_number = Column(String(20), unique=True, nullable=True, index=True,
                        comment='Primary contact number with country code')
    hashed_password = Column(String(255), nullable=False,
                           comment='Argon2 hashed password')
    salt = Column(String(255), nullable=False,
                 comment='Cryptographic salt for password hashing')
    
    # Multi-Factor Authentication
    mfa_enabled = Column(Boolean, default=False, nullable=False,
                        comment='Flag indicating if MFA is enabled for the user')
    mfa_method = Column(String(20), nullable=True,
                      comment='Primary MFA method (SMS, TOTP, Email, etc.)')
    mfa_secret = Column(String(100), nullable=True,
                      comment='Encrypted MFA secret for TOTP')
    backup_codes = Column(JSON, nullable=True,
                         comment='Encrypted backup codes for MFA recovery')
    last_mfa_verification = Column(DateTime(timezone=True), nullable=True,
                                 comment='Timestamp of last successful MFA verification')
    
    # Profile Information
    first_name = Column(String(100), nullable=False,
                      comment='Legal first name of the user')
    middle_name = Column(String(100), nullable=True,
                       comment='Middle name or initial if applicable')
    last_name = Column(String(100), nullable=False,
                     comment='Legal last name or family name')
    date_of_birth = Column(SQLDate, nullable=False,
                         comment='Date of birth for age verification and KYC')
    gender = Column(String(20), nullable=True,
                  comment='Self-identified gender (optional)')
    preferred_language = Column(String(10), default='en',
                             comment='Preferred language for communication')
    timezone = Column(String(50), default='UTC',
                    comment='User\'s preferred timezone')
    
    # Profile Media
    profile_picture_url = Column(String(512), nullable=True,
                              comment='URL to the user\'s profile picture')
    signature_url = Column(String(512), nullable=True,
                         comment='URL to the user\'s digital signature')
    
    # Customer Information
    customer_number = Column(String(50), unique=True, nullable=True, index=True,
                          comment='Unique customer identification number')
    customer_segment = Column(SQLEnum(CustomerSegment), default=CustomerSegment.RETAIL, nullable=False)
    risk_profile = Column(SQLEnum(RiskProfile), default=RiskProfile.NOT_ASSESSED, nullable=False)
    kyc_status = Column(SQLEnum(KYCStatus), default=KYCStatus.NOT_STARTED, nullable=False)
    credit_score = Column(Integer, nullable=True)
    annual_income = Column(Numeric(15, 2), nullable=True)
    net_worth = Column(Numeric(20, 2), nullable=True)
    
    # Security & Access Control
    role = Column(SQLEnum(UserRole), default=UserRole.CUSTOMER, 
                nullable=False, index=True,
                comment='User role for access control and permissions')
    status = Column(SQLEnum(UserStatus), default=UserStatus.PENDING_VERIFICATION, 
                  nullable=False, index=True,
                  comment='Current account status')
    
    # Authentication & Session Management
    last_login_at = Column(DateTime(timezone=True), nullable=True,
                         comment='Timestamp of last successful login')
    last_login_ip = Column(String(45), nullable=True,
                         comment='IP address from last login')
    last_failed_login = Column(DateTime(timezone=True), nullable=True,
                             comment='Timestamp of last failed login attempt')
    failed_login_attempts = Column(Integer, default=0, nullable=False,
                                 comment='Consecutive failed login attempts')
    last_password_change = Column(DateTime(timezone=True), nullable=True,
                                comment='When the password was last changed')
    password_expires_at = Column(DateTime(timezone=True), nullable=True,
                               comment='When the current password expires')
    
    # Device & Session Security
    trusted_devices = Column(JSON, nullable=True,
                           comment='List of trusted device identifiers')
    last_device_verification = Column(DateTime(timezone=True), nullable=True,
                                    comment='When device verification was last performed')
    
    # Security Questions & Recovery
    security_questions = Column(JSON, nullable=True,
                              comment='Encrypted security questions and answers')
    recovery_email = Column(String(255), nullable=True,
                          comment='Alternative email for account recovery')
    recovery_phone = Column(String(20), nullable=True,
                          comment='Alternative phone for account recovery')
    
    # Account Lockout & Restrictions
    account_locked_until = Column(DateTime(timezone=True), nullable=True,
                                 comment='Temporary account lock expiration')
    suspicious_activity_detected = Column(Boolean, default=False, nullable=False,
                                        comment='Flag for potential security issues')
    suspicious_activity_details = Column(JSON, nullable=True,
                                       comment='Details about suspicious activities')
    
    # Contact Information
    address = Column(JSON, nullable=True, comment='Primary address in structured format')
    
    # Multiple Addresses
    addresses = Column(
        JSON,
        nullable=True,
        default=list,
        comment='Array of user addresses in JSON format'
    )
    
    # Communication Channels
    phone_numbers = Column(JSON, default=[], nullable=False,
                         comment='All associated phone numbers with types and verification status')
    emails = Column(JSON, default=[], nullable=False,
                  comment='All associated email addresses with verification status')
    
    # Emergency & Trusted Contacts
    emergency_contacts = Column(JSON, default=[], nullable=False,
                              comment='Emergency contact information')
    trusted_contacts = Column(JSON, default=[], nullable=False,
                            comment='Trusted contacts for verification')
    
    # Social Media & Digital Presence
    social_profiles = Column(JSON, nullable=True,
                           comment='Connected social media accounts')
    
    # Preferred Contact Methods
    preferred_contact_method = Column(String(20), default='email',
                                    comment='Preferred method for communication')
    contact_time_windows = Column(JSON, nullable=True,
                                comment='Preferred time windows for contact')
    
    # Employment & Professional Information
    employment_status = Column(String(50), nullable=True, index=True,
                             comment='Current employment status')
    employer_name = Column(String(200), nullable=True, index=True,
                         comment='Current employer/organization name')
    job_title = Column(String(200), nullable=True,
                     comment='Current job title/position')
    employment_start_date = Column(SQLDate, nullable=True,
                                 comment='Employment start date')
    employment_end_date = Column(SQLDate, nullable=True,
                               comment='Employment end date (if applicable)')
    
    # Professional Details
    industry = Column(String(100), nullable=True,
                    comment='Industry/sector of employment')
    occupation = Column(String(100), nullable=True,
                      comment='Professional occupation category')
    years_in_employment = Column(Integer, nullable=True,
                               comment='Years in current employment')
    years_in_industry = Column(Integer, nullable=True,
                             comment='Total years in current industry')
    
    # Income & Employment Verification
    income_verification_status = Column(String(50), nullable=True,
                                      comment='Status of income verification')
    income_verification_date = Column(DateTime(timezone=True), nullable=True,
                                    comment='When income was last verified')
    employment_verification_status = Column(String(50), nullable=True,
                                          comment='Status of employment verification')
    
    # Previous Employment
    previous_employers = Column(JSON, nullable=True,
                              comment='Employment history')
    
    # Professional References
    professional_references = Column(JSON, nullable=True,
                                   comment='Professional references')
    
    # Identity Verification
    email_verified = Column(Boolean, default=False, nullable=False,
                          comment='Primary email verification status')
    email_verified_at = Column(DateTime(timezone=True), nullable=True,
                             comment='When primary email was verified')
    
    phone_verified = Column(Boolean, default=False, nullable=False,
                          comment='Primary phone verification status')
    phone_verified_at = Column(DateTime(timezone=True), nullable=True,
                             comment='When primary phone was verified')
    
    # Identity Documents
    id_verification_status = Column(String(50), nullable=True, index=True,
                                 comment='Overall identity verification status')
    id_verification_date = Column(DateTime(timezone=True), nullable=True,
                                comment='When identity was last verified')
    id_document_type = Column(String(50), nullable=True,
                            comment='Type of primary ID document')
    id_document_number = Column(String(100), nullable=True, index=True,
                              comment='Primary ID document number')
    id_document_issuer = Column(String(100), nullable=True,
                              comment='Issuing authority of primary ID')
    id_document_issue_date = Column(SQLDate, nullable=True,
                                  comment='When primary ID was issued')
    id_document_expiry = Column(SQLDate, nullable=True,
                              comment='Primary ID expiration date')
    id_document_front_url = Column(String(512), nullable=True,
                                 comment='URL to front of ID document')
    id_document_back_url = Column(String(512), nullable=True,
                                comment='URL to back of ID document')
    id_document_selfie_url = Column(String(512), nullable=True,
                                  comment='URL to selfie with ID document')
    
    # Secondary Identity Verification
    secondary_id_type = Column(String(50), nullable=True,
                             comment='Type of secondary ID document')
    secondary_id_number = Column(String(100), nullable=True,
                               comment='Secondary ID document number')
    
    # Tax & Regulatory Information
    tax_id = Column(String(100), nullable=True, index=True,
                  comment='Primary tax identification number')
    tax_id_type = Column(String(50), nullable=True,
                       comment='Type of tax ID (SSN, TIN, PAN, etc.)')
    tax_country = Column(String(2), nullable=True,
                       comment='Country of tax residence')
    tax_forms = Column(JSON, nullable=True,
                      comment='List of tax forms on file (W-9, W-8BEN, etc.)')
    
    # Regulatory Status
    is_fatca_compliant = Column(Boolean, default=False, nullable=False,
                              comment='FATCA compliance status')
    is_crs_compliant = Column(Boolean, default=False, nullable=False,
                            comment='CRS compliance status')
    regulatory_flags = Column(JSON, nullable=True,
                            comment='Regulatory flags or designations')
    
    # Compliance & AML
    aml_risk_score = Column(Integer, nullable=True,
                          comment='Anti-Money Laundering risk score')
    aml_risk_level = Column(String(20), nullable=True,
                          comment='Risk level (Low, Medium, High)')
    aml_last_checked = Column(DateTime(timezone=True), nullable=True,
                            comment='When AML check was last performed')
    
    # Sanctions & PEP Screening
    sanctions_check_status = Column(String(50), nullable=True,
                                 comment='Sanctions screening status')
    pep_status = Column(String(50), nullable=True,
                      comment='Politically Exposed Person status')
    adverse_media_status = Column(String(50), nullable=True,
                                comment='Adverse media screening status')
    
    # Consent Management
    consent_status = Column(
        JSON,
        default={
            'terms_of_service': False,
            'privacy_policy': False,
            'electronic_communications': False,
            'data_sharing': False,
            'marketing': False
        },
        nullable=False,
        comment='User consent status for various policies'
    )
    
    # Preferences & Settings
    preferences = Column(
        JSON,
        nullable=True,
        default=dict,
        comment='User preferences and settings'
    )
    
    # Relationships
    accounts = relationship('Account', back_populates='user', 
                          cascade='all, delete-orphan',
                          lazy='dynamic',
                          order_by='desc(Account.created_at)')
    
    cards = relationship('Card', back_populates='user',
                       cascade='all, delete-orphan',
                       lazy='dynamic',
                       order_by='desc(Card.created_at)')
    
    transactions = relationship('Transaction', back_populates='user',
                              cascade='all, delete-orphan',
                              lazy='dynamic',
                              order_by='desc(Transaction.transaction_date)')
    
    behavioral_patterns = relationship('BehavioralPattern', back_populates='user',
                                     cascade='all, delete-orphan',
                                     lazy='dynamic',
                                     order_by='desc(BehavioralPattern.detected_at)')
    
    ai_recommendations = relationship('AIRecommendation', back_populates='user',
                                    cascade='all, delete-orphan',
                                    lazy='dynamic',
                                    order_by='desc(AIRecommendation.generated_at)')
    
    fraud_alerts = relationship('FraudAlert', back_populates='user',
                              cascade='all, delete-orphan',
                              lazy='dynamic',
                              order_by='desc(FraudAlert.raised_at)')
    
    # Audit Relationships
    created_accounts = relationship('Account', 
                                  foreign_keys='[Account.created_by]',
                                  back_populates='creator')
    
    updated_accounts = relationship('Account',
                                  foreign_keys='[Account.updated_by]',
                                  back_populates='updater')
    
    # Session Management
    sessions = relationship('UserSession', back_populates='user',
                          cascade='all, delete-orphan',
                          lazy='dynamic')
    
    # Audit Logs
    activity_logs = relationship('UserActivityLog', back_populates='user',
                               cascade='all, delete-orphan',
                               lazy='dynamic')
    
    # Authentication
    auth_tokens = relationship('AuthToken', back_populates='user',
                             cascade='all, delete-orphan',
                             lazy='dynamic')
    
    # Security Events
    security_events = relationship('SecurityEvent', back_populates='user',
                                 cascade='all, delete-orphan',
                                 lazy='dynamic',
                                 order_by='desc(SecurityEvent.occurred_at)')
    
    # User Groups & Roles (for RBAC)
    user_roles = relationship('UserRole', back_populates='user',
                            cascade='all, delete-orphan',
                            lazy='dynamic')
    
    # User Preferences (for fine-grained control)
    user_preferences = relationship('UserPreference', back_populates='user',
                                  cascade='all, delete-orphan',
                                  lazy='dynamic')
    
    loans = relationship("Loan", back_populates="user", cascade="all, delete-orphan")
    
    # Audit fields
    created_by = Column(Integer, ForeignKey('users.id'), nullable=True)
    updated_by = Column(Integer, ForeignKey('users.id'), nullable=True)
    metadata_ = Column('metadata', JSON, default=dict)  # For additional attributes
    
    # Audit Fields
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False,
                      comment='Timestamp when the user account was created')
    created_by = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=True,
                      comment='User ID of the creator (for admin-created accounts)')
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), 
                      onupdate=func.now(), nullable=False,
                      comment='Timestamp of the last update')
    updated_by = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=True,
                      comment='User ID of the last updater')
    last_activity_at = Column(DateTime(timezone=True), nullable=True,
                            comment='Timestamp of the last user activity')
    last_password_change = Column(DateTime(timezone=True), nullable=True,
                                comment='When the password was last changed')
    
    # Soft Delete Fields
    deleted_at = Column(DateTime(timezone=True), nullable=True,
                      comment='Timestamp when the user was soft-deleted')
    deleted_by = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=True,
                      comment='User ID who performed the soft delete')
    deletion_reason = Column(String(255), nullable=True,
                          comment='Reason for account deletion')
    
    # Versioning & Concurrency
    version_id = Column(Integer, default=0, nullable=False,
                      comment='Version number for optimistic concurrency control')
    __mapper_args__ = {
        'version_id_col': version_id,
        'version_id_generator': lambda version: version + 1 if version else 1
    }
    
    # Table Configuration
    __table_args__ = (
        # Core indexes
        Index('idx_user_email', 'email', unique=True, 
              sqlite_where=(Column('email_verified') == 1),
              mssql_where=(Column('email_verified') == 1)),
        Index('idx_user_phone', 'phone_number', unique=True,
              sqlite_where=(Column('phone_verified') == 1),
              mssql_where=(Column('phone_verified') == 1)),
        Index('idx_user_status', 'status', 'last_login_at'),
        
        # Performance indexes
        Index('idx_user_name', 'first_name', 'last_name'),
        Index('idx_user_created', 'created_at'),
        
        # Check constraints with database-agnostic syntax
        Index('idx_user_fts',
             func.to_tsvector('english', 
                             func.coalesce(first_name, '') + ' ' +
                             func.coalesce(middle_name, '') + ' ' +
                             func.coalesce(last_name, '') + ' ' +
                             func.coalesce(email, '') + ' ' +
                             func.coalesce(phone_number, '') + ' ' +
                             func.coalesce(customer_number, '')),
             postgresql_using='gin'),
        
        # Check Constraints
        CheckConstraint(
            "email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}$'",
            name='valid_email_format'
        ),
        CheckConstraint(
            "phone_number IS NULL OR phone_number ~* '^\\+?[0-9\\s-]+$'",
            name='valid_phone_format'
        ),
        CheckConstraint(
            "date_of_birth <= CURRENT_DATE - INTERVAL '18 years'",
            name='user_must_be_adult'
        ),
        CheckConstraint(
            "failed_login_attempts BETWEEN 0 AND 10",
            name='valid_failed_login_attempts'
        ),
        
        # Conditional Constraints
        CheckConstraint(
            "(deleted_at IS NULL) OR (deleted_at IS NOT NULL AND deleted_by IS NOT NULL)",
            name='deletion_requires_deleted_by'
        ),
        {'extend_existing': True}
    )

    @property
    def full_name(self) -> str:
        """Return the full name of the user."""
        if self.middle_name:
            return f"{self.first_name} {self.middle_name} {self.last_name}"
        return f"{self.first_name} {self.last_name}"
    
    @property
    def age(self) -> Optional[int]:
        """Calculate and return the user's age based on date of birth."""
        if not self.date_of_birth:
            return None
        today = date.today()
        return today.year - self.date_of_birth.year - ((today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day))
    
    def is_kyc_verified(self) -> bool:
        """Check if the user's KYC is verified."""
        return self.kyc_status == KYCStatus.VERIFIED
    
    def is_high_risk(self) -> bool:
        """Check if the user is considered high risk."""
        return self.risk_profile in [RiskProfile.AGGRESSIVE, RiskProfile.NOT_ASSESSED] or \
               self.status in [UserStatus.SUSPENDED, UserStatus.FRAUD_HOLD]
    
    def get_preferred_contact_method(self) -> Dict[str, Any]:
        """Get the user's preferred contact method from preferences."""
        if not self.communication_preferences:
            return {"method": "email", "value": self.email}
            
        preferred = self.communication_preferences.get("preferred_contact", {})
        method = preferred.get("method", "email")
        
        if method == "email":
            return {"method": "email", "value": self.email}
        elif method == "phone" and self.phone_number:
            return {"method": "phone", "value": self.phone_number}
        else:
            return {"method": "email", "value": self.email}
    
    def to_dict(self, include_sensitive: bool = False) -> Dict[str, Any]:
        """Convert user model to dictionary."""
        data = {
            "user_id": self.id,
            "customer_number": self.customer_number,
            "first_name": self.first_name,
            "middle_name": self.middle_name,
            "last_name": self.last_name,
            "full_name": self.full_name,
            "email": self.email,
            "phone_number": self.phone_number,
            "date_of_birth": self.date_of_birth.isoformat() if self.date_of_birth else None,
            "age": self.age,
            "gender": self.gender,
            "profile_picture_url": self.profile_picture_url,
            "customer_segment": self.customer_segment.value if self.customer_segment else None,
            "risk_profile": self.risk_profile.value if self.risk_profile else None,
            "kyc_status": self.kyc_status.value if self.kyc_status else None,
            "credit_score": self.credit_score,
            "annual_income": float(self.annual_income) if self.annual_income is not None else None,
            "net_worth": float(self.net_worth) if self.net_worth is not None else None,
            "role": self.role.value if self.role else None,
            "status": self.status.value if self.status else None,
            "employment_status": self.employment_status,
            "employer_name": self.employer_name,
            "job_title": self.job_title,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_login_at": self.last_login_at.isoformat() if self.last_login_at else None,
            "is_kyc_verified": self.is_kyc_verified(),
            "is_high_risk": self.is_high_risk()
        }
        
        if include_sensitive:
            data.update({
                "phone_verified": self.phone_verified,
                "email_verified": self.email_verified,
                "id_verification_status": self.id_verification_status,
                "id_document_type": self.id_document_type,
                "id_document_number": self.id_document_number,
                "id_document_expiry": self.id_document_expiry.isoformat() if self.id_document_expiry else None,
                "tax_id": self.tax_id,
                "communication_preferences": self.communication_preferences,
                "notification_preferences": self.notification_preferences,
                "privacy_preferences": self.privacy_preferences,
                "is_deleted": self.is_deleted,
                "deleted_at": self.deleted_at.isoformat() if self.deleted_at else None
            })
        
        return data
    
    def __repr__(self) -> str:
        return f"<User(id={self.id}, customer_number={self.customer_number}, email={self.email}, role={self.role})>"
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.email})"
    
    @property
    def initials(self) -> str:
        """Return the user's initials."""
        return f"{self.first_name[0]}{self.last_name[0]}".upper()
    
    @property
    def is_active(self) -> bool:
        """Check if the user is active."""
        return self.status == UserStatus.ACTIVE
    
    @property
    def is_verified(self) -> bool:
        """Check if the user's email is verified."""
        return self.email_verified
    
    @property
    def is_locked(self) -> bool:
        """Check if the user's account is locked."""
        return self.status == UserStatus.LOCKED or (
            self.account_locked_until is not None and 
            self.account_locked_until > datetime.now(timezone.utc)
        )
    
    @property
    def needs_password_reset(self) -> bool:
        """Check if the user needs to reset their password."""
        if not self.last_password_change:
            return True
        return (
            self.password_expires_at is not None and
            self.password_expires_at < datetime.now(timezone.utc)
        )
    
    @property
    def mfa_enabled(self) -> bool:
        """Check if MFA is enabled for the user."""
        return bool(self.mfa_secret) and self._mfa_enabled
    
    def has_role(self, role_name: Union[str, UserRole]) -> bool:
        """Check if the user has the specified role."""
        if isinstance(role_name, str):
            role_name = UserRole(role_name)
        return self.role == role_name
    
    def has_any_role(self, *roles: Union[str, UserRole]) -> bool:
        """Check if the user has any of the specified roles."""
        role_values = [r.value if isinstance(r, UserRole) else r for r in roles]
        return self.role in role_values
    
    def has_permission(self, permission: str) -> bool:
        """Check if the user has the specified permission."""
        # This would typically check against the user's roles and permissions
        # For now, we'll just check against some basic permissions
        if self.role == UserRole.ADMIN:
            return True
        
        # Add more permission checks as needed
        return False
    
    def get_audit_info(self) -> Dict[str, Any]:
        """Get audit information about the user."""
        return {
            'user_id': str(self.id),
            'email': self.email,
            'customer_number': self.customer_number,
            'status': self.status.value,
            'role': self.role.value,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login_at': self.last_login_at.isoformat() if self.last_login_at else None,
            'failed_login_attempts': self.failed_login_attempts,
            'mfa_enabled': self.mfa_enabled,
            'email_verified': self.email_verified,
            'phone_verified': self.phone_verified,
            'kyc_status': self.kyc_status.value if self.kyc_status else None,
            'risk_profile': self.risk_profile.value if self.risk_profile else None,
            'customer_segment': self.customer_segment.value if self.customer_segment else None,
            'is_active': self.is_active,
            'is_locked': self.is_locked,
            'needs_password_reset': self.needs_password_reset,
            'account_ids': [str(acc.id) for acc in self.accounts],
            'card_ids': [str(card.id) for card in self.cards],
            'transaction_count': self.transactions.count() if hasattr(self.transactions, 'count') else 0,
            'behavioral_patterns_count': self.behavioral_patterns.count() if hasattr(self.behavioral_patterns, 'count') else 0,
            'ai_recommendations_count': self.ai_recommendations.count() if hasattr(self.ai_recommendations, 'count') else 0,
            'fraud_alerts_count': self.fraud_alerts.count() if hasattr(self.fraud_alerts, 'count') else 0,
        }


class Session(ModelBase):
    """
    User session model for tracking active sessions with enhanced security features.
    """
    __tablename__ = "user_sessions"
    
    # Primary key
    id = Column(UUID, primary_key=True, default=uuid4, index=True, unique=True, nullable=False)
    
    # Core session data
    user_id = Column(UUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    session_id = Column(String(100), unique=True, nullable=False, index=True)
    token = Column(String(512), unique=True, nullable=False, index=True)
    refresh_token = Column(String(512), unique=True, nullable=True, index=True)
    
    # Device and location information
    ip_address = Column(String(45), nullable=True)  # IPv6 can be up to 45 chars
    user_agent = Column(Text, nullable=True)
    device_id = Column(String(255), nullable=True, index=True)
    device_name = Column(String(100), nullable=True)
    device_type = Column(String(50), nullable=True)  # mobile, tablet, desktop, etc.
    os = Column(String(50), nullable=True)
    browser = Column(String(100), nullable=True)
    
    # Location data
    country_code = Column(String(10), nullable=True)
    region = Column(String(100), nullable=True)
    city = Column(String(100), nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    
    # Session status and timing
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    last_activity = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Security flags
    is_compromised = Column(Boolean, default=False, nullable=False)
    force_logout = Column(Boolean, default=False, nullable=False)
    
    # Metadata
    metadata_ = Column('metadata', JSON, default=dict)  # For additional attributes
    
    # Relationships
    user = relationship("User", back_populates="sessions")
    
    # Indexes
    __table_args__ = (
        Index('idx_session_token', 'token', postgresql_using='hash'),
        Index('idx_refresh_token', 'refresh_token', postgresql_using='hash'),
        Index('idx_session_user', 'user_id', 'is_active'),
        Index('idx_session_device', 'device_id', 'device_type'),
        Index('idx_session_expiry', 'expires_at', postgresql_where=Column('is_active') == True),
    )
    
    @property
    def is_expired(self) -> bool:
        """Check if the session has expired."""
        from datetime import datetime, timezone
        return datetime.now(timezone.utc) > self.expires_at
    
    @property
    def location(self) -> Dict[str, Any]:
        """Get location information as a dictionary."""
        return {
            'ip_address': self.ip_address,
            'country_code': self.country_code,
            'region': self.region,
            'city': self.city,
            'coordinates': {
                'latitude': self.latitude,
                'longitude': self.longitude
            } if self.latitude and self.longitude else None
        }
    
    @property
    def device_info(self) -> Dict[str, Any]:
        """Get device information as a dictionary."""
        return {
            'device_id': self.device_id,
            'device_name': self.device_name,
            'device_type': self.device_type,
            'os': self.os,
            'browser': self.browser,
            'user_agent': self.user_agent
        }
    
    def mark_compromised(self, reason: str = None):
        """Mark the session as potentially compromised."""
        self.is_compromised = True
        self.is_active = False
        if reason:
            if 'security_events' not in self.metadata_:
                self.metadata_['security_events'] = []
            self.metadata_['security_events'].append({
                'type': 'session_compromised',
                'timestamp': datetime.utcnow().isoformat(),
                'reason': reason
            })
    
    def to_dict(self, include_token: bool = False) -> Dict[str, Any]:
        """Convert session to dictionary."""
        data = {
            'session_id': self.session_id,
            'user_id': self.user_id,
            'is_active': self.is_active,
            'is_expired': self.is_expired,
            'is_compromised': self.is_compromised,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'last_activity': self.last_activity.isoformat() if self.last_activity else None,
            'device': self.device_info,
            'location': self.location,
            'metadata': self.metadata_
        }
        
        if include_token:
            data['token'] = self.token
            if self.refresh_token:
                data['refresh_token'] = self.refresh_token
                
        return data
