"""
Database configuration and connection management.
"""

import os
import json
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings


print("Debug: Loading DatabaseConfig")
print(f"DB_HOST from env: {os.getenv('DB_HOST')}")
print(f"DB_PORT from env: {os.getenv('DB_PORT')}")
print(f"DB_USER from env: {os.getenv('DB_USER')}")
print(f"DB_PASSWORD from env: {os.getenv('DB_PASSWORD')}")
print(f"DB_NAME from env: {os.getenv('DB_NAME')}")
print(f"DATABASE_URL from env: {os.getenv('DATABASE_URL')}")


class DatabaseConfig(BaseSettings):
    """Database configuration settings."""
    
    # PostgreSQL connection - explicit field names that will read from DB_HOST, DB_PORT, etc.
    host: str = Field(default="localhost")
    port: int = Field(default=5432)
    name: str = Field(default="ai_knowledge_agent")
    user: str = Field(default="postgres")
    password: str = Field(default="postgres")
    
    # DATABASE_URL for Secrets Manager integration
    database_url_env: Optional[str] = Field(default=None, env="DATABASE_URL", validation_alias="DATABASE_URL")
    
    # Connection pool settings
    pool_size: int = Field(default=10, env="DB_POOL_SIZE")
    max_overflow: int = Field(default=20, env="DB_MAX_OVERFLOW")
    pool_timeout: int = Field(default=30, env="DB_POOL_TIMEOUT")
    
    # Async settings
    echo: bool = Field(default=False, env="DB_ECHO")
    echo_pool: bool = Field(default=False, env="DB_ECHO_POOL")
    
    # Migration settings
    migration_dir: str = Field(default="alembic", env="DB_MIGRATION_DIR")
    
    @property
    def database(self) -> str:
        """Alias for name field."""
        return self.name
    
    @property
    def username(self) -> str:
        """Alias for user field."""
        return self.user
    
    @property
    def database_url(self) -> str:
        """Get the database URL for SQLAlchemy."""
        # If DATABASE_URL is provided (from Secrets Manager), parse it
        if self.database_url_env:
            try:
                # Try to parse as JSON (from Secrets Manager)
                db_config = json.loads(self.database_url_env)
                user = db_config.get('username', 'postgres')
                password = db_config.get('password', '')
                host = db_config.get('host', 'localhost')
                port = db_config.get('port', '5432')
                database = db_config.get('dbname', 'ai_knowledge_agent')
                
                # Remove port from host if it's already included
                if ':' in host:
                    host = host.split(':')[0]
                
                # Build PostgreSQL URL
                if password:
                    return f"postgresql://{user}:{password}@{host}:{port}/{database}"
                else:
                    return f"postgresql://{user}@{host}:{port}/{database}"
            except json.JSONDecodeError:
                # If it's not JSON, assume it's already a proper URL
                if self.database_url_env.startswith('postgresql+asyncpg://'):
                    return self.database_url_env.replace('postgresql+asyncpg://', 'postgresql://')
                elif self.database_url_env.startswith('postgresql://'):
                    return self.database_url_env
                else:
                    return self.database_url_env
        
        # Fallback to individual components
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}"
    
    @property
    def async_database_url(self) -> str:
        """Get the async database URL for SQLAlchemy."""
        # If DATABASE_URL is provided (from Secrets Manager), parse it
        if self.database_url_env:
            try:
                # Try to parse as JSON (from Secrets Manager)
                db_config = json.loads(self.database_url_env)
                user = db_config.get('username', 'postgres')
                password = db_config.get('password', '')
                host = db_config.get('host', 'localhost')
                port = db_config.get('port', '5432')
                database = db_config.get('dbname', 'ai_knowledge_agent')
                
                # Remove port from host if it's already included
                if ':' in host:
                    host = host.split(':')[0]
                
                # Build async PostgreSQL URL
                if password:
                    return f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{database}"
                else:
                    return f"postgresql+asyncpg://{user}@{host}:{port}/{database}"
            except json.JSONDecodeError:
                # If it's not JSON, assume it's already a proper URL
                if self.database_url_env.startswith('postgresql+asyncpg://'):
                    return self.database_url_env
                elif self.database_url_env.startswith('postgresql://'):
                    return self.database_url_env.replace('postgresql://', 'postgresql+asyncpg://')
                else:
                    return self.database_url_env
        
        # Fallback to individual components
        return f"postgresql+asyncpg://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}"
    
    model_config = {
        "env_file": ".env.local",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
        "env_prefix": "DB_",  # All fields will look for DB_ prefixed env vars
    }


def get_database_config() -> DatabaseConfig:
    """Get database configuration instance."""
    config = DatabaseConfig()
    print(f"Debug: Constructed database_url: {config.database_url}")
    print(f"Debug: Constructed async_database_url: {config.async_database_url}")
    return config
