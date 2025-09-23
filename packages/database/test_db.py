#!/usr/bin/env python3
"""
Test script to verify database connection and basic operations.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add src to path
SRC_DIR = Path(__file__).parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from src.database import get_db_client, get_async_session
from src.services import DocumentProcessingService, LoggingService
from src.models import ProcessingStatus, ProcessorType, FileType
from src.config import get_database_config


async def test_database_connection():
    """Test basic database connection and operations."""
    print("🔧 Testing database connection...")
    
    # Test configuration
    config = get_database_config()
    print(f"✅ Database config loaded: {config.host}:{config.port}/{config.database}")
    
    # Test client
    client = get_db_client()
    print("✅ Database client created")
    
    # Test async session
    async with client.async_session() as session:
        print("✅ Async session created successfully")
        
        # Test service layer
        service = DocumentProcessingService(session)
        logging_service = LoggingService(session)
        
        print("✅ Service layer initialized")
        
        # Test creating a simple ingestion job
        job = await service.create_ingestion_job(
            collection_name="test_collection",
            file_paths=["test_file.pdf"],
            metadata={"test": True, "source": "test_script"},
            created_by="test_user"
        )
        
        print(f"✅ Created test ingestion job: {job.id}")
        
        # Test logging
        log_entry = await logging_service.log_processing_event(
            level="INFO",
            message="Test log entry",
            ingestion_job_id=job.id,
            processor_type="test",
            processing_stage="initialization"
        )
        
        print(f"✅ Created test log entry: {log_entry.id}")
        
        # Test getting job
        retrieved_job = await service.get_ingestion_job(job.id)
        if retrieved_job:
            print(f"✅ Retrieved job successfully: {retrieved_job.status}")
        else:
            print("❌ Failed to retrieve job")
        
        # Test listing jobs
        jobs = await service.list_jobs(limit=5)
        print(f"✅ Listed {len(jobs)} jobs")
        
        # Test statistics
        stats = await service.get_processing_statistics()
        print(f"✅ Retrieved statistics: {len(stats)} categories")
        
        print("\n🎉 All database tests passed!")
        
        return True


async def test_model_enums():
    """Test that model enums work correctly."""
    print("\n🔧 Testing model enums...")
    
    # Test ProcessingStatus
    status = ProcessingStatus.PENDING
    print(f"✅ ProcessingStatus: {status.value}")
    
    # Test ProcessorType
    processor = ProcessorType.GPT_4O
    print(f"✅ ProcessorType: {processor.value}")
    
    # Test FileType
    file_type = FileType.PDF
    print(f"✅ FileType: {file_type.value}")
    
    print("✅ All enum tests passed!")


async def main():
    """Run all tests."""
    print("🚀 Starting database tests...\n")
    
    try:
        # Load environment variables
        env_file = Path(__file__).parent / "database.env"
        if env_file.exists():
            with open(env_file) as f:
                for line in f:
                    if line.strip() and not line.startswith('#'):
                        key, value = line.strip().split('=', 1)
                        os.environ[key] = value
        
        await test_model_enums()
        await test_database_connection()
        
        print("\n🎉 All tests completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)


