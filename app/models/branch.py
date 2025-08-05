"""
Branch model for bank branches.
"""
from enum import Enum
from datetime import time
from typing import Optional

from sqlalchemy import (
    Column, String, Integer, Boolean, JSON, 
    ForeignKey, DateTime, Time, Index, Enum as SQLEnum, Numeric
)
from sqlalchemy.orm import relationship

from .base import ModelBase


class BranchType(str, Enum):
    """Types of bank branches."""
    MAIN = "main"
    BRANCH = "branch"
    ATM = "atm"
    KIOSK = "kiosk"
    CORPORATE = "corporate"
    PRIVATE = "private"
    FOREIGN = "foreign"


class BranchStatus(str, Enum):
    """Branch status values."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    TEMPORARILY_CLOSED = "temporarily_closed"
    UNDER_MAINTENANCE = "under_maintenance"


class Branch(ModelBase):
    """Bank branch model."""
    
    __tablename__ = "branches"
    
    # Primary Key
    id = Column(Integer, primary_key=True, autoincrement=True)
    # Branch identification
    branch_code = Column(String(10), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    branch_type = Column(SQLEnum(BranchType), default=BranchType.BRANCH, nullable=False)
    status = Column(SQLEnum(BranchStatus), default=BranchStatus.ACTIVE, nullable=False)
    
    # Contact information
    phone = Column(String(20), nullable=True)
    email = Column(String(255), nullable=True)
    
    # Address
    address_line1 = Column(String(255), nullable=False)
    address_line2 = Column(String(255), nullable=True)
    city = Column(String(100), nullable=False, index=True)
    state = Column(String(100), nullable=False, index=True)
    postal_code = Column(String(20), nullable=True)
    country = Column(String(100), default="India", nullable=False)
    
    # Location
    latitude = Column(Numeric(10, 8), nullable=True)
    longitude = Column(Numeric(11, 8), nullable=True)
    
    # Operational details
    ifsc_code = Column(String(20), unique=True, nullable=False, index=True)
    micr_code = Column(String(20), nullable=True)
    
    # Working hours (stored as JSON for flexibility)
    working_hours = Column(JSON, nullable=True)
    
    # Manager information
    manager_name = Column(String(100), nullable=True)
    manager_contact = Column(String(20), nullable=True)
    
    # Additional metadata
    is_24x7 = Column(Boolean, default=False, nullable=False)
    has_atm = Column(Boolean, default=False, nullable=False)
    has_locker = Column(Boolean, default=False, nullable=False)
    has_wifi = Column(Boolean, default=False, nullable=False)
    is_wheelchair_accessible = Column(Boolean, default=False, nullable=False)
    
    # Relationships
    accounts = relationship("Account", back_populates="branch")
    employees = relationship("Employee", back_populates="branch")
    
    # Indexes
    __table_args__ = (
        Index('idx_branch_location', 'city', 'state'),
        Index('idx_branch_code', 'branch_code', unique=True),
        Index('idx_branch_ifsc', 'ifsc_code', unique=True),
        {'extend_existing': True}
    )
    
    @property
    def full_address(self) -> str:
        """Return the full address as a formatted string."""
        parts = [
            self.address_line1,
            self.address_line2,
            f"{self.city}, {self.state}",
            self.postal_code,
            self.country
        ]
        return ", ".join(filter(None, parts))
    
    def __repr__(self) -> str:
        return f"<Branch(id={self.id}, name={self.name}, city={self.city})>"


class EmployeeRole(str, Enum):
    """Employee roles within a branch."""
    BRANCH_MANAGER = "branch_manager"
    ASSISTANT_MANAGER = "assistant_manager"
    TELLER = "teller"
    CUSTOMER_SERVICE = "customer_service"
    OPERATIONS = "operations"
    LOAN_OFFICER = "loan_officer"
    RELATIONSHIP_MANAGER = "relationship_manager"
    SECURITY = "security"
    OTHER = "other"


class Employee(ModelBase):
    """Bank employee model."""
    
    __tablename__ = "employees"
    
    # Primary Key
    id = Column(Integer, primary_key=True, autoincrement=True)
    # Employee identification
    employee_id = Column(String(20), unique=True, nullable=False, index=True)
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    
    # Role and department
    role = Column(SQLEnum(EmployeeRole), nullable=False)
    department = Column(String(50), nullable=True)
    
    # Contact information
    email = Column(String(255), unique=True, nullable=False)
    phone = Column(String(20), nullable=True)
    
    # Employment details
    join_date = Column(DateTime, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Branch relationship
    branch_id = Column(Integer, ForeignKey("branches.id"), nullable=False)
    branch = relationship("Branch", back_populates="employees")
    
    # User account (if employee has access to system)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    user = relationship("User", back_populates="employee_profile")
    
    @property
    def full_name(self) -> str:
        """Return the employee's full name."""
        return f"{self.first_name} {self.last_name}"
    
    def __repr__(self) -> str:
        return f"<Employee(id={self.id}, name={self.full_name}, role={self.role})>"
