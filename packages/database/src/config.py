"""
Database configuration and connection management.
"""

import os
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings


class DatabaseConfig(BaseSettings):
    """Database configuration settings."""
    
    # PostgreSQL connection
    host: str = Field(default="localhost", env="DB_HOST")
    port: int = Field(default=5432, env="DB_PORT")
    database: str = Field(default="ai_knowledge_agent", env="DB_NAME")
    username: str = Field(default="postgres", env="DB_USER")
    password: str = Field(default="postgres", env="DB_PASSWORD")
    
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
    def database_url(self) -> str:
        """Get the database URL for SQLAlchemy."""
        return f"postgresql://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"
    
    @property
    def async_database_url(self) -> str:
        """Get the async database URL for SQLAlchemy."""
        return f"postgresql+asyncpg://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


def get_database_config() -> DatabaseConfig:
    """Get database configuration instance."""
    return DatabaseConfig()
