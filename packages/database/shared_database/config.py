"""
Database configuration and connection management.
"""

import os
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings


print("Debug: Loading DatabaseConfig")
print(f"DB_HOST from env: {os.getenv('DB_HOST')}")
print(f"DB_PORT from env: {os.getenv('DB_PORT')}")
print(f"DB_USER from env: {os.getenv('DB_USER')}")
print(f"DB_PASSWORD from env: {os.getenv('DB_PASSWORD')}")
print(f"DB_NAME from env: {os.getenv('DB_NAME')}")


class DatabaseConfig(BaseSettings):
    """Database configuration settings."""
    
    # PostgreSQL connection - explicit field names that will read from DB_HOST, DB_PORT, etc.
    host: str = Field(default="localhost")
    port: int = Field(default=5432)
    name: str = Field(default="ai_knowledge_agent")
    user: str = Field(default="postgres")
    password: str = Field(default="postgres")
    
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
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}"
    
    @property
    def async_database_url(self) -> str:
        """Get the async database URL for SQLAlchemy."""
        # Plain URL - SSL handling moved to connect_args in database.py
        return f"postgresql+asyncpg://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}"
    
    model_config = {
        "env_file": ".env.local",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
        "env_prefix": "DB_",  # All fields will look for DB_ prefixed env vars
    }


def get_database_config() -> DatabaseConfig:
    """Get database configuration instance."""
    return DatabaseConfig()
