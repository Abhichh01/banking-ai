"""
Base model for SQLAlchemy models with Azure SQL compatibility.
"""
from datetime import datetime
from typing import Any, Dict, Optional, Type, TypeVar

from sqlalchemy import Column, DateTime, MetaData
from sqlalchemy.ext.declarative import as_declarative, declared_attr
from sqlalchemy.sql import func

# Recommended naming convention for constraints and indexes
# See: https://alembic.sqlalchemy.org/en/latest/naming.html
naming_convention = {
    "ix": 'ix_%(column_0_label)s',
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}

# Create metadata with naming convention
metadata = MetaData(naming_convention=naming_convention)

# Type variable for model classes
ModelType = TypeVar('ModelType', bound='ModelBase')

# Import the database-agnostic types
from app.db.types import JSON, UUID, Interval  # noqa: E402, F401


@as_declarative(metadata=metadata)
class ModelBase:
    """Base class for all SQLAlchemy models."""
    
    id: Any
    __name__: str
    
    # Generate __tablename__ automatically
    @declared_attr
    def __tablename__(cls) -> str:
        return cls.__name__.lower()
    
    # Standard columns with timezone support
    created_at = Column(DateTime(timezone=True), 
                      server_default=func.now(), 
                      nullable=False,
                      comment='Timestamp when the record was created')
    updated_at = Column(DateTime(timezone=True), 
                      onupdate=func.now(), 
                      nullable=True,
                      comment='Timestamp when the record was last updated')
    
    def to_dict(self, exclude: Optional[set] = None) -> Dict[str, Any]:
        """Convert model to dictionary."""
        exclude = exclude or set()
        return {
            column.name: getattr(self, column.name)
            for column in self.__table__.columns
            if column.name not in exclude
        }
    
    def update(self, **kwargs) -> None:
        """Update model attributes.
        
        Args:
            **kwargs: Attributes to update
            
        Example:
            user.update(first_name='John', last_name='Doe')
        """
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        self.updated_at = datetime.utcnow()
        
    @classmethod
    def get_table_name(cls) -> str:
        """Get the table name for this model.
        
        Returns:
            str: The table name
        """
        return cls.__tablename__
        
    @classmethod
    def get_primary_key(cls) -> str:
        """Get the primary key column name for this model.
        
        Returns:
            str: The primary key column name
        """
        return cls.__table__.primary_key.columns[0].name


from app.schemas.user import User
from app.schemas.account import Account
from app.schemas.transaction import Transaction