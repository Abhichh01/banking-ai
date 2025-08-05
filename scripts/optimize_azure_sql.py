"""
Azure SQL Database Optimization Script

This script applies database optimizations for Azure SQL Database including:
1. Creating indexes on frequently queried fields
2. Updating statistics
3. Rebuilding or reorganizing indexes
4. Applying query store settings
5. Setting up maintenance tasks
"""
import logging
import pyodbc
from typing import List, Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class AzureSqlOptimizer:
    """Class to handle Azure SQL Database optimizations."""
    
    def __init__(self, connection_string: str):
        """Initialize with a connection string."""
        self.connection_string = connection_string
        self.connection = None
        self.cursor = None
    
    def connect(self):
        """Establish database connection."""
        try:
            self.connection = pyodbc.connect(self.connection_string)
            self.cursor = self.connection.cursor()
            logger.info("Successfully connected to Azure SQL Database")
        except Exception as e:
            logger.error(f"Failed to connect to database: {str(e)}")
            raise
    
    def close(self):
        """Close database connection."""
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()
        logger.info("Database connection closed")
    
    def execute_sql(self, sql: str, params: Optional[tuple] = None) -> List[Dict[str, Any]]:
        """Execute SQL query and return results as a list of dictionaries."""
        try:
            if params:
                self.cursor.execute(sql, params)
            else:
                self.cursor.execute(sql)
                
            # If it's a SELECT query, fetch results
            if sql.strip().upper().startswith('SELECT'):
                columns = [column[0] for column in self.cursor.description]
                return [dict(zip(columns, row)) for row in self.cursor.fetchall()]
            else:
                self.connection.commit()
                return []
                
        except Exception as e:
            self.connection.rollback()
            logger.error(f"Error executing SQL: {str(e)}")
            raise
    
    def create_index(self, table: str, columns: List[str], index_name: str, 
                    unique: bool = False, include_columns: Optional[List[str]] = None):
        """Create an index on the specified columns."""
        columns_str = ", ".join(columns)
        unique_str = "UNIQUE" if unique else ""
        include_str = ""
        
        if include_columns:
            include_str = f" INCLUDE ({', '.join(include_columns)})"
            
        sql = f"""
        IF NOT EXISTS (SELECT * FROM sys.indexes 
                      WHERE name = '{index_name}' AND object_id = OBJECT_ID('{table}'))
        BEGIN
            CREATE {unique_str} INDEX {index_name} 
            ON {table} ({columns_str}){include_str};
            PRINT 'Created index {index_name} on {table}({columns_str})';
        END
        """
        
        logger.info(f"Creating index {index_name} on {table}({columns_str})")
        self.execute_sql(sql)
    
    def update_statistics(self, table: str = None):
        """Update statistics for a specific table or all tables."""
        if table:
            sql = f"UPDATE STATISTICS {table} WITH FULLSCAN"
            logger.info(f"Updating statistics for table: {table}")
            self.execute_sql(sql)
        else:
            # Update statistics for all tables
            sql = """
            DECLARE @sql NVARCHAR(MAX) = N'';
            SELECT @sql = @sql + 'UPDATE STATISTICS ' 
                + QUOTENAME(s.name) + '.' + QUOTENAME(t.name) + ' WITH FULLSCAN; '
            FROM sys.tables t
            INNER JOIN sys.schemas s ON t.schema_id = s.schema_id;
            EXEC sp_executesql @sql;
            """
            logger.info("Updating statistics for all tables")
            self.execute_sql(sql)
    
    def rebuild_or_reorganize_indexes(self, rebuild_threshold: int = 30):
        """Rebuild or reorganize indexes based on fragmentation."""
        logger.info(f"Checking index fragmentation (rebuild threshold: {rebuild_threshold}%)")
        
        # Get fragmented indexes
        sql = f"""
        SELECT 
            SCHEMA_NAME(t.schema_id) AS schema_name,
            t.name AS table_name,
            i.name AS index_name,
            ips.avg_fragmentation_in_percent
        FROM sys.dm_db_index_physical_stats(DB_ID(), NULL, NULL, NULL, 'LIMITED') ips
        INNER JOIN sys.tables t ON ips.object_id = t.object_id
        INNER JOIN sys.indexes i ON ips.object_id = i.object_id AND ips.index_id = i.index_id
        WHERE ips.avg_fragmentation_in_percent > 10  -- Only consider if > 10% fragmented
        AND ips.page_count > 1000  -- Only consider if more than 1000 pages
        ORDER BY ips.avg_fragmentation_in_percent DESC;
        """
        
        indexes = self.execute_sql(sql)
        
        for idx in indexes:
            full_name = f"{idx['schema_name']}.{idx['table_name']}.{idx['index_name']}"
            frag = idx['avg_fragmentation_in_percent']
            
            if frag >= rebuild_threshold:
                logger.info(f"Rebuilding index {full_name} ({frag:.2f}% fragmented)")
                self.execute_sql(f"ALTER INDEX [{idx['index_name']}] ON [{idx['schema_name']}].[{idx['table_name']}] REBUILD")
            else:
                logger.info(f"Reorganizing index {full_name} ({frag:.2f}% fragmented)")
                self.execute_sql(f"ALTER INDEX [{idx['index_name']}] ON [{idx['schema_name']}].[{idx['table_name']}] REORGANIZE")
    
    def enable_query_store(self):
        """Enable and configure Query Store if not already enabled."""
        logger.info("Configuring Query Store")
        
        # Check if Query Store is enabled
        sql = """
        SELECT actual_state_desc, desired_state_desc, current_storage_size_mb, 
               max_storage_size_mb, readonly_reason, interval_length_minutes,
               stale_query_threshold_days, size_based_cleanup_mode_desc
        FROM sys.database_query_store_options;
        """
        
        result = self.execute_sql(sql)
        
        if not result:
            # Enable Query Store with recommended settings
            sql = """
            ALTER DATABASE CURRENT 
            SET QUERY_STORE = ON 
            (
                OPERATION_MODE = READ_WRITE, 
                CLEANUP_POLICY = (STALE_QUERY_THRESHOLD_DAYS = 30), 
                DATA_FLUSH_INTERVAL_SECONDS = 900, 
                MAX_STORAGE_SIZE_MB = 1024, 
                INTERVAL_LENGTH_MINUTES = 60, 
                SIZE_BASED_CLEANUP_MODE = AUTO, 
                QUERY_CAPTURE_MODE = AUTO, 
                MAX_PLANS_PER_QUERY = 200
            );
            """
            self.execute_sql(sql)
            logger.info("Query Store has been enabled with recommended settings")
        else:
            logger.info("Query Store is already enabled")
    
    def create_missing_indexes(self):
        """Create missing indexes based on query optimizer recommendations."""
        logger.info("Checking for missing indexes")
        
        sql = """
        SELECT TOP 20
            ROUND(s.avg_total_user_cost * s.avg_user_impact * (s.user_seeks + s.user_scans), 0) AS [Total Cost],
            d.statement AS [Table Name],
            d.equality_columns,
            d.inequality_columns,
            d.included_columns,
            s.unique_compiles,
            s.user_seeks,
            s.user_scans,
            s.last_user_seek,
            s.last_user_scan
        FROM sys.dm_db_missing_index_details d
        INNER JOIN sys.dm_db_missing_index_groups g ON d.index_handle = g.index_handle
        INNER JOIN sys.dm_db_missing_index_group_stats s ON g.index_group_handle = s.group_handle
        WHERE d.database_id = DB_ID()
        ORDER BY [Total Cost] DESC;
        """
        
        missing_indexes = self.execute_sql(sql)
        
        for i, idx in enumerate(missing_indexes, 1):
            table_name = idx['Table Name'].replace('[', '').replace(']', '')
            index_name = f'IX_{table_name}_{i}'
            
            columns = []
            if idx['equality_columns']:
                columns.append(idx['equality_columns'].replace('[', '').replace(']', ''))
            if idx['inequality_columns']:
                columns.append(idx['inequality_columns'].replace('[', '').replace(']', ''))
            
            include_columns = []
            if idx['included_columns']:
                include_columns = [col.strip() for col in idx['included_columns'].split(',')]
            
            if columns:
                self.create_index(
                    table=table_name,
                    columns=columns,
                    index_name=index_name,
                    include_columns=include_columns
                )
    
    def optimize_database(self):
        """Run all optimization tasks."""
        try:
            self.connect()
            
            # 1. Enable and configure Query Store
            self.enable_query_store()
            
            # 2. Create recommended indexes
            self.create_missing_indexes()
            
            # 3. Rebuild or reorganize indexes based on fragmentation
            self.rebuild_or_reorganize_indexes()
            
            # 4. Update statistics
            self.update_statistics()
            
            logger.info("Database optimization completed successfully")
            
        except Exception as e:
            logger.error(f"Error during database optimization: {str(e)}")
            raise
        finally:
            self.close()

def get_connection_string() -> str:
    """Get connection string from environment variables."""
    import os
    from dotenv import load_dotenv
    
    # Load environment variables from .env in the project root
    project_root = Path(__file__).parent.parent
    load_dotenv(project_root / '.env')
    
    # Get connection details from environment variables
    server = os.getenv('DB_SERVER')
    database = os.getenv('DB_NAME')
    username = os.getenv('DB_USER')
    password = os.getenv('DB_PASSWORD')
    
    if not all([server, database, username, password]):
        raise ValueError("Missing required database connection details in environment variables")
    
    # Construct connection string
    return f"""
    Driver={{ODBC Driver 18 for SQL Server}};
    Server=tcp:{server},1433;
    Database={database};
    Uid={username};
    Pwd={password};
    Encrypt=yes;
    TrustServerCertificate=no;
    Connection Timeout=30;
    """

if __name__ == "__main__":
    try:
        # Get connection string
        conn_str = get_connection_string()
        
        # Initialize and run optimizer
        optimizer = AzureSqlOptimizer(conn_str)
        optimizer.optimize_database()
        
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
        sys.exit(1)
