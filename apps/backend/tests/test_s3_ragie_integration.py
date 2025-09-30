"""
Test script for S3 + Ragie integration.

This script tests the new S3+URL upload flow for Ragie document processing.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from services.ragie_s3_service import get_ragie_s3_service, RagieS3ServiceError
from adapters.ragie_client import RagieClient
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_s3_ragie_integration():
    """Test the S3 + Ragie integration flow."""
    
    logger.info("🧪 Starting S3 + Ragie integration test")
    
    # Check environment variables
    required_env_vars = [
        "RAGIE_API_KEY",
        "AWS_ACCESS_KEY_ID", 
        "AWS_SECRET_ACCESS_KEY"
    ]
    
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]
    if missing_vars:
        logger.error(f"❌ Missing required environment variables: {missing_vars}")
        logger.info("💡 Please set these in your .env.local file:")
        for var in missing_vars:
            logger.info(f"   {var}=your_value_here")
        return False
    
    logger.info("✅ All required environment variables are set")
    
    try:
        # Initialize the S3 Ragie service
        logger.info("🔧 Initializing RagieS3Service...")
        ragie_s3_service = get_ragie_s3_service()
        logger.info("✅ RagieS3Service initialized successfully")
        
        # Test organization bucket creation
        test_org_id = "test-org-123"
        logger.info(f"🪣 Testing bucket creation for organization: {test_org_id}")
        
        bucket_name = await ragie_s3_service.ensure_organization_bucket(test_org_id)
        logger.info(f"✅ Organization bucket ready: {bucket_name}")
        
        # Create a test file
        test_content = b"This is a test document for S3 + Ragie integration testing."
        test_filename = "test_document.txt"
        test_user_id = "test-user-456"
        
        logger.info(f"📄 Testing document upload: {test_filename}")
        
        # Test the upload flow (this will create S3 file and send URL to Ragie)
        document, s3_url = await ragie_s3_service.upload_document_for_ragie(
            file_content=test_content,
            filename=test_filename,
            organization_id=test_org_id,
            user_id=test_user_id,
            metadata={"test": True, "integration_test": "s3_ragie"}
        )
        
        logger.info("✅ Document upload successful!")
        logger.info(f"   Document ID: {document.id}")
        logger.info(f"   Document Status: {document.status}")
        logger.info(f"   Document Name: {document.name}")
        logger.info(f"   S3 URL: {s3_url[:100]}...")
        
        # Test cleanup (optional - comment out if you want to keep the test file)
        logger.info("🧹 Testing S3 cleanup...")
        cleanup_success = await ragie_s3_service.cleanup_s3_file(s3_url, test_org_id)
        
        if cleanup_success:
            logger.info("✅ S3 cleanup successful")
        else:
            logger.warning("⚠️ S3 cleanup failed (this is not critical)")
        
        logger.info("🎉 S3 + Ragie integration test completed successfully!")
        return True
        
    except RagieS3ServiceError as e:
        logger.error(f"❌ RagieS3Service error: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Unexpected error during test: {e}")
        logger.exception("Full traceback:")
        return False


async def test_bucket_naming():
    """Test the bucket naming logic."""
    
    logger.info("🧪 Testing bucket naming logic")
    
    try:
        ragie_s3_service = get_ragie_s3_service()
        
        test_cases = [
            ("simple-org", "ragie-docs-simpleorg"),
            ("org_with_underscores", "ragie-docs-orgwithunderscores"),
            ("ORG-WITH-CAPS", "ragie-docs-orgwithcaps"),
            ("complex-org_123", "ragie-docs-complexorg123")
        ]
        
        for org_id, expected_bucket in test_cases:
            actual_bucket = ragie_s3_service.get_organization_bucket_name(org_id)
            if actual_bucket == expected_bucket:
                logger.info(f"✅ {org_id} -> {actual_bucket}")
            else:
                logger.error(f"❌ {org_id} -> {actual_bucket} (expected: {expected_bucket})")
                return False
        
        logger.info("✅ Bucket naming test passed!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Bucket naming test failed: {e}")
        return False


if __name__ == "__main__":
    async def main():
        # Load environment variables from .env.local
        from dotenv import load_dotenv
        load_dotenv(Path(__file__).parent.parent / ".env.local")
        
        logger.info("🚀 Starting S3 + Ragie Integration Tests")
        
        # Test 1: Bucket naming logic
        bucket_test_passed = await test_bucket_naming()
        
        # Test 2: Full integration (only if bucket test passed)
        if bucket_test_passed:
            integration_test_passed = await test_s3_ragie_integration()
            
            if integration_test_passed:
                logger.info("🎉 All tests passed! S3 + Ragie integration is working correctly.")
                sys.exit(0)
            else:
                logger.error("❌ Integration test failed.")
                sys.exit(1)
        else:
            logger.error("❌ Bucket naming test failed.")
            sys.exit(1)
    
    asyncio.run(main())
