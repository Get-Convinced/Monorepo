#!/usr/bin/env python3
"""
Test script to verify database integration with document processor.
"""

import asyncio
import os
import sys
import tempfile
from pathlib import Path
from uuid import UUID

# Add src to path
SRC_DIR = Path(__file__).parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

# Import database and processor components
from shared_database import (
    DatabaseClient, 
    get_async_session,
    ProcessingStatus,
    DocumentProcessingService,
    LoggingService
)
from embeddings import EmbeddingService, OllamaEmbeddingProvider
from rag.vector_store import VectorStore
from workers.database_ingestion_worker import DatabaseIngestionWorker
from processors.unified_document_processor import GPTModel


async def test_database_integration():
    """Test database integration with document processing."""
    print("🔧 Testing database integration with document processor...")
    
    # Load environment variables
    env_file = Path(__file__).parent.parent / "packages" / "database" / "database.env"
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                if line.strip() and not line.startswith('#'):
                    key, value = line.strip().split('=', 1)
                    os.environ[key] = value
    
    # Initialize database client
    db_client = DatabaseClient()
    print("✅ Database client initialized")
    
    # Initialize services
    embedding_service = EmbeddingService.create_ollama_provider(
        base_url="http://localhost:11434",
        model="mxbai-embed-large"
    )
    vector_store = VectorStore(qdrant_url="http://localhost:6336")
    print("✅ Services initialized")
    
    # Create a test document
    test_content = """
    This is a test document for database integration.
    
    It contains multiple paragraphs to test document processing.
    
    The document should be processed and stored in the database.
    """
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write(test_content)
        test_file_path = f.name
    
    try:
        # Test database session and worker
        async with db_client.async_session() as session:
            print("✅ Database session created")
            
            # Initialize database ingestion worker
            worker = DatabaseIngestionWorker(
                db_session=session,
                embedding_service=embedding_service,
                vector_store=vector_store,
                openai_api_key="test-key",  # Won't be used for txt files
                gpt_model=GPTModel.GPT_4O,
                use_unified_worker=True
            )
            print("✅ Database ingestion worker initialized")
            
            # Create a test job
            job_id = await worker.create_job(
                file_paths=[test_file_path],
                collection_name="test_collection",
                metadata={"test": True, "source": "integration_test"},
                created_by="test_user"
            )
            print(f"✅ Created test job: {job_id}")
            
            # Get job status
            job_status = await worker.get_job_status(job_id)
            if job_status:
                print(f"✅ Retrieved job status: {job_status['status']}")
            else:
                print("❌ Failed to retrieve job status")
                return False
            
            # List jobs
            jobs = await worker.list_jobs(limit=5)
            print(f"✅ Listed {len(jobs)} jobs")
            
            # Get processing statistics
            stats = await worker.get_processing_statistics()
            print(f"✅ Retrieved processing statistics: {len(stats)} categories")
            
            # Test logging service
            logging_service = LoggingService(session)
            log_entry = await logging_service.log_processing_event(
                level="INFO",
                message="Database integration test completed",
                ingestion_job_id=job_id,
                processor_type="integration_test",
                processing_stage="test_completion"
            )
            print(f"✅ Created test log entry: {log_entry.id}")
            
            print("\n🎉 Database integration test completed successfully!")
            return True
            
    except Exception as e:
        print(f"\n❌ Database integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        # Clean up test file
        if os.path.exists(test_file_path):
            os.unlink(test_file_path)


async def test_database_models():
    """Test that database models work correctly."""
    print("\n🔧 Testing database models...")
    
    try:
        from shared_database import ProcessingStatus, ProcessorType
        
        # Test enums
        status = ProcessingStatus.PENDING
        processor = ProcessorType.GPT_4O
        
        print(f"✅ ProcessingStatus: {status.value}")
        print(f"✅ ProcessorType: {processor.value}")
        
        # Test database config
        from shared_database import DatabaseConfig
        config = DatabaseConfig()
        print(f"✅ Database config: {config.host}:{config.port}/{config.database}")
        
        print("✅ Database models test passed!")
        return True
        
    except Exception as e:
        print(f"❌ Database models test failed: {e}")
        return False


async def main():
    """Run all integration tests."""
    print("🚀 Starting database integration tests...\n")
    
    try:
        # Test database models first
        models_ok = await test_database_models()
        if not models_ok:
            print("❌ Database models test failed, skipping integration test")
            return False
        
        # Test full integration
        integration_ok = await test_database_integration()
        
        if integration_ok:
            print("\n🎉 All database integration tests passed!")
            print("\n📊 Integration Summary:")
            print("✅ Database connection working")
            print("✅ Models and enums working")
            print("✅ Database ingestion worker working")
            print("✅ Job creation and retrieval working")
            print("✅ Logging service working")
            print("✅ Processing statistics working")
            print("\n🚀 Ready for production use!")
        else:
            print("\n❌ Database integration tests failed!")
        
        return integration_ok
        
    except Exception as e:
        print(f"\n❌ Test suite failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)


