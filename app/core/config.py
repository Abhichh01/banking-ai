"""Application configuration settings.

This module contains all the configuration settings for the application,
including database connections, security settings, and third-party API keys.
"""

from functools import lru_cache
from typing import List, Optional, Any, Union
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
import json

class Settings(BaseSettings):
    """Application settings."""
    
    # Application settings
    API_V1_STR: str 
    PROJECT_NAME: str 
    API_VERSION: str 
    DEBUG: bool = False
    ENVIRONMENT: str = "development"
    SECRET_KEY: str = "your-secret-key-here"  # Change in production
    
    # CORS settings
    CORS_ORIGINS: List[str] = ["*"]
    CORS_ORIGIN_REGEX: str = ""
    ALLOWED_HOSTS: List[str] = ["*"]
    
    # Server Configuration
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    
    # Database Configuration (Azure SQL)
    DB_SERVER: str = Field(..., env="DB_SERVER")
    DB_NAME: str = Field(..., env="DB_NAME")
    DB_USER: str = Field(..., env="DB_USER")
    DB_PASSWORD: str = Field(..., env="DB_PASSWORD")
    
    # API Keys
    API_KEY: Optional[str] = None
    API_URL: Optional[str] = None
    
    # Session settings
    SESSION_COOKIE_NAME: Optional[str] = None
    SESSION_LIFETIME: Optional[int] = None
    SESSION_SAME_SITE: Optional[str] = None
    SESSION_HTTPS_ONLY: Optional[bool] = None
    SESSION_DOMAIN: Optional[str] = None

    # Rate limiting
    RATE_LIMIT: Optional[int] = None

    # Additional API Keys
    GPT_MODEL_NAME: Optional[str] = None
    CLAUDE_OPUS_MODEL_NAME: Optional[str] = None
    CLAUDE_SONNET_MODEL_NAME: Optional[str] = None
    LLAMA_MODEL_NAME: Optional[str] = None
    TEXT_EMBEDDINGS_MODEL_NAME: Optional[str] = None

    # Model Configuration
    LOCAL_MODEL_PATH: Optional[str] = None
    LLM_DEFAULT_MODEL: str = "gpt-4o"
    
    # Model paths
    DATABASE_MODELS_PATH: str = "./app/models"
    # Logging
    LOG_LEVEL: str = "INFO"
    
    # Azure SQL specific settings
    AZURE_SQL_ENCRYPT: bool = True
    AZURE_SQL_TRUST_SERVER_CERTIFICATE: bool = False
    AZURE_SQL_CONNECTION_TIMEOUT: int = 30
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
        env_prefix=""
    )
    
    @property
    def DATABASE_URL(self) -> str:
        """Generate the database URL from settings."""
        # URL-encode the connection string components
        from urllib.parse import quote_plus
        
        # Build the connection string
        conn_str = (
            f"Driver={{ODBC Driver 18 for SQL Server}};"
            f"Server=tcp:{self.DB_SERVER},1433;"
            f"Database={self.DB_NAME};"
            f"Uid={self.DB_USER};"
            f"Pwd={self.DB_PASSWORD};"
            "Encrypt=yes;"
            "TrustServerCertificate=no;"
            "Connection Timeout=30;"
        )
        
        # URL-encode the connection string
        quoted_conn_str = quote_plus(conn_str)
        
        # Return the SQLAlchemy URL
        return f"mssql+pyodbc:///?odbc_connect={quoted_conn_str}"
        
    @field_validator("AZURE_SQL_ENCRYPT", "AZURE_SQL_TRUST_SERVER_CERTIFICATE", mode='before')
    @classmethod
    def validate_azure_sql_bool(cls, v: Any) -> str:
        """Convert boolean to 'yes'/'no' for Azure SQL."""
        if isinstance(v, bool):
            return "yes" if v else "no"
        if isinstance(v, str):
            return v.lower()
        return "no"
    
    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: Any) -> List[str]:
        """Parse CORS origins from string to list."""
        if isinstance(v, list):
            return v
        if isinstance(v, str):
            if v.startswith("[") and v.endswith("]"):
                try:
                    return json.loads(v)
                except json.JSONDecodeError:
                    pass
            return [origin.strip() for origin in v.split(",")]
        return ["*"]  # Default to allow all
    
@lru_cache()
def get_settings() -> Settings:
    """
    Get application settings.
    Returns:
        Settings: Application settings
    """
    return Settings()
