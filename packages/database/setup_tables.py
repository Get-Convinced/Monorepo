#!/usr/bin/env python3
"""
Simple script to create database tables for the AI Knowledge Agent.
"""
import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine
from src.models import Base

async def create_tables():
    """Create all database tables."""
    # Database configuration
    db_url = "postgresql+asyncpg://postgres:postgres@localhost:5432/ai_knowledge_agent"
    
    print("🔗 Connecting to database...")
    engine = create_async_engine(db_url, echo=True)
    
    print("📊 Creating tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    print("✅ Tables created successfully!")
    
    # Test connection
    async with engine.begin() as conn:
        result = await conn.execute("SELECT 1")
        print(f"🧪 Database connection test: {result.scalar()}")
    
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(create_tables())
