"""
Database type definitions with Azure SQL compatibility.

This module provides database-agnostic type definitions that work across different
SQL databases, with specific optimizations for Azure SQL.
"""
from __future__ import annotations

import json
from datetime import timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional, Type, TypeVar, Union

"""
Custom SQLAlchemy types for the Banking AI application.
"""
import json
from typing import Any, Optional, TypeVar, Union

from sqlalchemy import types
from sqlalchemy.dialects.mssql import UNIQUEIDENTIFIER
from sqlalchemy.engine import Dialect
from sqlalchemy.types import TypeDecorator

T = TypeVar('T')

class JSON(TypeDecorator):
    """Custom JSON type optimized for Azure SQL.
    
    Uses NVARCHAR(MAX) with ISJSON constraint for validation.
    Automatically handles JSON serialization/deserialization.
    """
    impl = types.NVARCHAR
    cache_ok = True

    def load_dialect_impl(self, dialect: Dialect) -> types.TypeEngine:
        # Always use NVARCHAR(MAX) for Azure SQL
        return dialect.type_descriptor(types.NVARCHAR(max_=2**31-1))

    def process_bind_param(self, value: Any, dialect: Dialect) -> Optional[str]:
        if value is None:
            return None
        return json.dumps(value, default=str, ensure_ascii=False)

    def process_result_value(self, value: Any, dialect: Dialect) -> Optional[Union[dict, list]]:
        if value is None:
            return None
        try:
            return json.loads(value)
        except (TypeError, json.JSONDecodeError):
            return value
        if dialect.name == 'postgresql' or isinstance(value, (dict, list)):
            return value
        try:
            return json.loads(value) if value else None
        except (TypeError, ValueError):
            return None


class UUID(TypeDecorator):
    """UUID type optimized for Azure SQL.
    
    Uses UNIQUEIDENTIFIER in Azure SQL with proper string conversion.
    Falls back to UUID in PostgreSQL for compatibility.
    """
    impl = types.CHAR(36)  # Fixed length for UNIQUEIDENTIFIER string representation
    cache_ok = True

    def load_dialect_impl(self, dialect: Dialect) -> types.TypeEngine:
        if dialect.name == 'mssql':
            # Use UNIQUEIDENTIFIER for Azure SQL
            return dialect.type_descriptor(UNIQUEIDENTIFIER())
        # Fall back to native UUID for PostgreSQL
        return dialect.type_descriptor(types.UUID())

    def process_bind_param(self, value: Any, dialect: Dialect) -> Optional[str]:
        if value is None:
            return None
        
        # Convert to string and ensure proper format
        uuid_str = str(value).lower().replace('-', '')
        
        if dialect.name == 'mssql':
            # For Azure SQL, ensure proper UNIQUEIDENTIFIER format
            return f"{{{value.upper()}}}" if value else None
            
        return str(value).lower()

    def process_result_value(self, value: Any, dialect: Dialect) -> Optional[str]:
        if value is None:
            return None
            
        # Convert to lowercase string and remove any surrounding braces
        uuid_str = str(value).lower().strip('{}')
        
        # Ensure proper UUID format (8-4-4-4-12)
        if len(uuid_str) == 32:  # If no hyphens
            uuid_str = f"{uuid_str[:8]}-{uuid_str[8:12]}-{uuid_str[12:16]}-{uuid_str[16:20]}-{uuid_str[20:]}"
            
        return uuid_str


class Interval(TypeDecorator):
    """Interval type optimized for Azure SQL.
    
    Stores intervals as BIGINT seconds in Azure SQL for precise calculations.
    Falls back to INTERVAL in PostgreSQL for compatibility.
    """
    impl = types.BIGINT
    cache_ok = True

    def load_dialect_impl(self, dialect: Dialect) -> types.TypeEngine:
        if dialect.name == 'mssql':
            # Use BIGINT for Azure SQL to store seconds
            return dialect.type_descriptor(types.BIGINT())
        # Fall back to native INTERVAL for PostgreSQL
        return dialect.type_descriptor(types.Interval())

    def process_bind_param(self, value: Any, dialect: Dialect) -> Optional[int]:
        if value is None:
            return None
            
        if dialect.name == 'postgresql':
            return value
            
        # Convert timedelta to total seconds for Azure SQL
        if isinstance(value, timedelta):
            return int(value.total_seconds())
            
        # Handle string input like '1 day', '2 hours', etc.
        if isinstance(value, str):
            # Simple parser for common interval formats
            parts = value.split()
            if len(parts) == 2 and parts[1] in ('seconds', 'second'):
                return int(parts[0])
            elif len(parts) == 2 and parts[1] in ('minutes', 'minute'):
                return int(parts[0]) * 60
            elif len(parts) == 2 and parts[1] in ('hours', 'hour'):
                return int(parts[0]) * 3600
            elif len(parts) == 2 and parts[1] in ('days', 'day'):
                return int(parts[0]) * 86400
                
        return int(value) if value is not None else None

    def process_result_value(self, value: Any, dialect: Dialect) -> Optional[timedelta]:
        if value is None:
            return None
            
        if dialect.name == 'postgresql':
            return value
            
        # Convert seconds back to timedelta for Azure SQL
        return timedelta(seconds=int(value))


# Export common types for easy access
JSON = JSON
UUID = UUID
Interval = Interval
