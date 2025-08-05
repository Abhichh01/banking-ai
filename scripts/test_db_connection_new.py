"""Test script to verify the new async database connection and schema.
"""
import os
import sys
import asyncio
import pyodbc
from pathlib import Path
from sqlalchemy.sql import text

# Change to the project root directory
project_root = Path(__file__).parent.parent
os.chdir(project_root)

# Add project root to path
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


from app.core.config import get_settings
from app.db.database import Database, Base

async def test_database_connection():
    """Test async database connection and basic operations."""
    settings = get_settings()
    
    # Print debug info
    print("Testing async database connection with settings:")
    print(f"DB_SERVER: {settings.DB_SERVER}")
    print(f"DB_NAME: {settings.DB_NAME}")
    print(f"DB_USER: {settings.DB_USER}")
    print(f"DATABASE_URL: {settings.DATABASE_URL[:50]}...")
    
    # Test direct pyodbc connection first
    try:
        print("\nTesting direct pyodbc connection...")
        conn_str = f'''
            Driver={{ODBC Driver 18 for SQL Server}};
            Server=tcp:{settings.DB_SERVER},1433;
            Database={settings.DB_NAME};
            Uid={settings.DB_USER};
            Pwd={settings.DB_PASSWORD};
            Encrypt=yes;
            TrustServerCertificate=no;
            Connection Timeout=30;
        '''
        with pyodbc.connect(conn_str) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sys.tables")
            tables = cursor.fetchall()
            print(f"✅ Direct pyodbc connection successful! Found {len(tables)} tables")
    except Exception as e:
        print(f"❌ Direct pyodbc connection failed: {str(e)}")
        return False
    
    # Test async SQLAlchemy connection
    print("\nTesting async SQLAlchemy connection...")
    try:
        db = Database()
        
        # Test raw async connection first
        print("Testing raw async connection...")
        try:
            async with db.async_engine.connect() as conn:
                # Use fetchone() and close the result set explicitly
                result = await conn.execute(text("SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES"))
                count = result.scalar()
                print(f"✅ Raw async connection test successful. Found {count} tables")
        except Exception as e:
            print(f"❌ Raw async connection test failed: {str(e)}")
            return False
        
        # Test async session creation
        print("Testing async session creation...")
        async with db.session_scope() as session:
            print("✅ Async session created successfully")
            
            # Test simple query with explicit result handling
            try:
                print("Testing simple async query...")
                # Use a simple query that returns a single row
                result = await session.execute(text("SELECT name FROM sys.tables"))
                row = result.fetchone()  # Explicitly fetch the row
                if row:
                    print(f"✅ Simple async query successful! Found {row[0]}")
                else:
                    print("❌ No results from simple async query")
                    return False
            except Exception as e:
                print(f"❌ Simple async query failed: {str(e)}")
                return False
            
            # Test table creation
            try:
                print("Testing async table creation...")
                await db.create_tables()
                print("✅ Async table creation successful")
            except Exception as e:
                print(f"❌ Async table creation failed: {str(e)}")
                return False
            print("✅ Database tables created successfully")
            
            # List all tables with proper result set handling
            try:
                async with db.async_engine.connect() as conn:
                    # Execute the query and await the result
                    result = await conn.execute(
                        text("SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE = 'BASE TABLE'")
                    )
                    tables = [row[0] for row in result]
                    print(f"✅ Found {len(tables)} tables: {', '.join(tables) if tables else 'None'}")
            except Exception as e:
                print(f"❌ Error listing tables: {str(e)}")
                # Continue with the test even if table listing fails
            
        return True
        
    except Exception as e:
        print(f"❌ Error during async database test: {str(e)}")
        return False
    finally:
        # Clean up (drop tables after test)
        if db.async_engine:
            try:
                print("\nCleaning up...")
                await db.drop_tables()
                print("✅ Cleanup complete")
            except Exception as e:
                print(f"⚠️  Error during cleanup: {e}")

async def main():
    """Main async function to run the test."""
    if await test_database_connection():
        print("\n✅ All async database tests passed!")
        return 0
    else:
        print("\n❌ Async database tests failed!")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

