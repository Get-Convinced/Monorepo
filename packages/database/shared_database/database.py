"""
Database client and connection management.
"""

import asyncio
from typing import AsyncGenerator, Optional
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import (
    AsyncSession, 
    create_async_engine, 
    async_sessionmaker,
    AsyncEngine
)
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

from .config import DatabaseConfig
from .models import Base


class DatabaseClient:
    """Database client for managing connections and sessions."""
    
    def __init__(self, config: DatabaseConfig):
        self.config = config
        self._async_engine: Optional[AsyncEngine] = None
        self._sync_engine = None
        self._async_session_factory: Optional[async_sessionmaker] = None
        self._sync_session_factory = None
    
    @property
    def async_engine(self) -> AsyncEngine:
        """Get or create async engine."""
        if self._async_engine is None:
            # Configure engine with pool_pre_ping to test connections
            self._async_engine = create_async_engine(
                self.config.async_database_url,
                echo=self.config.echo,
                echo_pool=self.config.echo_pool,
                pool_size=self.config.pool_size,
                max_overflow=self.config.max_overflow,
                pool_timeout=self.config.pool_timeout,
                pool_pre_ping=True,  # Test connections before using them
            )
        return self._async_engine
    
    @property
    def sync_engine(self):
        """Get or create sync engine."""
        if self._sync_engine is None:
            self._sync_engine = create_engine(
                self.config.database_url,
                echo=self.config.echo,
                echo_pool=self.config.echo_pool,
                pool_size=self.config.pool_size,
                max_overflow=self.config.max_overflow,
                pool_timeout=self.config.pool_timeout,
            )
        return self._sync_engine
    
    @property
    def async_session_factory(self) -> async_sessionmaker:
        """Get or create async session factory."""
        if self._async_session_factory is None:
            self._async_session_factory = async_sessionmaker(
                bind=self.async_engine,
                class_=AsyncSession,
                expire_on_commit=False
            )
        return self._async_session_factory
    
    @property
    def sync_session_factory(self):
        """Get or create sync session factory."""
        if self._sync_session_factory is None:
            self._sync_session_factory = sessionmaker(
                bind=self.sync_engine,
                expire_on_commit=False
            )
        return self._sync_session_factory
    
    async def create_tables(self) -> None:
        """Create all tables."""
        async with self.async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    
    async def drop_tables(self) -> None:
        """Drop all tables."""
        async with self.async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
    
    @asynccontextmanager
    async def async_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get async database session."""
        async with self.async_session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()
    
    @asynccontextmanager
    def sync_session(self):
        """Get sync database session."""
        with self.sync_session_factory() as session:
            try:
                yield session
                session.commit()
            except Exception:
                session.rollback()
                raise
            finally:
                session.close()
    
    async def close(self) -> None:
        """Close all connections."""
        if self._async_engine:
            await self._async_engine.dispose()
        if self._sync_engine:
            self._sync_engine.dispose()


# Global database client instance
_db_client: Optional[DatabaseClient] = None


def get_db_client() -> DatabaseClient:
    """Get global database client instance."""
    global _db_client
    if _db_client is None:
        from .config import get_database_config
        config = get_database_config()
        _db_client = DatabaseClient(config)
    return _db_client


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for FastAPI to get async database session."""
    async with get_db_client().async_session() as session:
        yield session


def get_sync_session():
    """Get sync database session."""
    return get_db_client().sync_session()


