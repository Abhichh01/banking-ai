"""
Database configuration and session management for Azure SQL.

This module provides a database connection manager with dependency injection
for SQLAlchemy async sessions, optimized for Azure SQL Database.
"""
import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional, Any

from sqlalchemy import create_engine, event, text
from sqlalchemy.engine import Engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.pool import QueuePool

from app.core.config import get_settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# SQLAlchemy base class for models
Base = declarative_base()

class Database:
    """Database connection manager for Azure SQL with async support."""
    
    def __init__(self) -> None:
        """Initialize the database connection manager."""
        self.settings = get_settings()
        self.engine: Optional[Engine] = None
        self.async_engine = None
        self.async_session_factory = None
        self._setup_async_engine()
        self._setup_event_listeners()
    
    def _setup_async_engine(self) -> None:
        """Configure and create the async SQLAlchemy engine."""
        if self.async_engine is not None:
            return
            
        # Convert DATABASE_URL to async format
        database_url = self.settings.DATABASE_URL
        if database_url.startswith('mssql+pyodbc://'):
            # Convert to async format
            async_database_url = database_url.replace('mssql+pyodbc://', 'mssql+aioodbc://')
        else:
            # Fallback for other database types
            async_database_url = database_url.replace('://', '+async://')
        
        # Configure engine with Azure SQL optimizations for async pyodbc
        connect_args = {
            'autocommit': False,
            'timeout': 30,
            'readonly': False,
            'autocommit_always': False,
            'connect_timeout': 30,
            'server_side_cursors': False,  # Disable server-side cursors
            'use_setinputsizes': False,    # Disable setinputsizes for better compatibility
            'use_scope_identity': True,    # Use SCOPE_IDENTITY() for lastrowid
            'fast_executemany': False,     # Disable fast_executemany as it can cause issues
            'stream_results': False,       # Disable streaming results
            'pool_pre_ping': True,         # Enable connection health checks
        }
        
        self.async_engine = create_async_engine(
            async_database_url,
            # Remove poolclass for async engines - let SQLAlchemy choose the appropriate pool
            pool_size=5,  # Default pool size
            max_overflow=10,  # Default max overflow
            pool_timeout=30,  # Default timeout in seconds
            pool_recycle=1800,  # Recycle connections after 30 minutes
            pool_pre_ping=True,  # Enable connection health checks
            echo=True,  # Enable SQL query logging for debugging
            future=True,  # Use SQLAlchemy 2.0 style APIs
            fast_executemany=False,  # Disable as it can cause issues with some ODBC drivers
            connect_args=connect_args,
        )
        
        # Create async session factory
        self.async_session_factory = async_sessionmaker(
            bind=self.async_engine,
            autocommit=False,
            autoflush=False,
            expire_on_commit=False,
            class_=AsyncSession,
        )
    
    def _setup_event_listeners(self) -> None:
        """Set up SQLAlchemy event listeners."""
        if self.async_engine is None:
            return
            
        @event.listens_for(Engine, 'before_cursor_execute')
        def receive_before_cursor_execute(
            conn, cursor, statement, params, context, executemany
        ):
            """Log SQL queries in development."""
            if self.settings.DEBUG:
                logger.debug("Executing query: %s", statement)
    
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get an async database session with dependency injection.
        
        Yields:
            AsyncSession: An async SQLAlchemy session
            
        Example:
            async with db.get_session() as session:
                result = await session.execute(select(User))
        """
        session: Optional[AsyncSession] = None
        try:
            if self.async_session_factory is None:
                raise RuntimeError("Database async session factory not initialized")
                
            session = self.async_session_factory()
            yield session
            await session.commit()
        except Exception as e:
            if session is not None:
                await session.rollback()
            logger.error("Database error: %s", str(e))
            raise
        finally:
            if session is not None:
                await session.close()
    
    @asynccontextmanager
    async def session_scope(self) -> AsyncGenerator[AsyncSession, None]:
        """Provide a transactional scope around a series of operations."""
        if self.async_session_factory is None:
            raise RuntimeError("Database async session factory not initialized")
            
        session = self.async_session_factory()
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
    
    async def create_tables(self) -> None:
        """Create all database tables."""
        if self.async_engine is None:
            raise RuntimeError("Database async engine not initialized")
            
        async with self.async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables created successfully")
    
    async def drop_tables(self) -> None:
        """Drop all database tables. Use with caution!"""
        if self.async_engine is None:
            raise RuntimeError("Database async engine not initialized")
            
        async with self.async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        logger.warning("Dropped all database tables")
    
    async def execute_raw_sql(self, sql: str, params: Optional[dict] = None) -> Any:
        """Execute raw SQL query.
        
        Args:
            sql: SQL query string
            params: Optional parameters for the query
            
        Returns:
            The result of the query execution
        """
        if self.async_engine is None:
            raise RuntimeError("Database async engine not initialized")
            
        async with self.async_engine.connect() as connection:
            result = await connection.execute(text(sql), params or {})
            return result
    
    async def health_check(self) -> bool:
        """Check if the database is accessible."""
        try:
            async with self.async_engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            return True
        except Exception as e:
            logger.error("Database health check failed: %s", str(e))
            return False
