"""
Database module initialization.
Provides async database session management and base model for SQLAlchemy with Azure SQL.
"""
from typing import AsyncGenerator, Optional

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from .database import Database

# Initialize the database instance
db = Database()

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=db.async_engine,
    class_=AsyncSession,
)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency that provides an async database session.
    
    Yields:
        AsyncSession: An async database session
    """
    session: Optional[AsyncSession] = None
    try:
        session = AsyncSessionLocal()
        yield session
    finally:
        if session is not None:
            await session.close()

# Export public API
__all__ = [
    'db',
    'AsyncSessionLocal',
    'get_db',
    'Base',
    'get_db',
    'get_db_session'
]