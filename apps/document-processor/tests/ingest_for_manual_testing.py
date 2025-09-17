#!/usr/bin/env python3
"""
One-time document ingestion script for manual RAG testing.
This script processes documents and stores them in a persistent collection
that won't be deleted during testing.
"""

import asyncio
import logging
import os
import sys
from pathlib import Path
from typing import List, Optional

# Add src to path
SRC_DIR = Path(__file__).parent.parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv('.env.local')
    load_dotenv('.env')
    load_dotenv('.env.test')
except ImportError:
    pass

from processors.unified_document_processor import GPTModel
from workers.unified_document_worker import UnifiedDocumentWorker
from embeddings import EmbeddingService
from rag.vector_store import VectorStore

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
PERSISTENT_COLLECTION = "manual_testing_kb"  # This collection won't be deleted
EMBED_DIMENSION = 1024
EMBED_MODEL = "mxbai-embed-large"
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6336")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GPT_MODEL = GPTModel.GPT_4O_MINI

# Test documents to process
TEST_DOCUMENTS = [
    "test_data/Bizom _ Discussion Deck.pdf",
    # Add more documents here as needed
]

class ManualIngestionService:
    """Service for one-time document ingestion for manual testing."""
    
    def __init__(self):
        self.vector_store = VectorStore(qdrant_url=QDRANT_URL)
        self.embedding_service = EmbeddingService.create_ollama_provider(
            base_url=OLLAMA_BASE_URL,
            model=EMBED_MODEL
        )
        self.worker = UnifiedDocumentWorker(
            embedding_service=self.embedding_service,
            vector_store=self.vector_store,
            openai_api_key=OPENAI_API_KEY,
            gpt_model=GPT_MODEL
        )
    
    async def setup_collection(self):
        """Setup the persistent collection for manual testing."""
        try:
            await self.vector_store.ensure_collection_exists(
                PERSISTENT_COLLECTION, 
                EMBED_DIMENSION
            )
            logger.info(f"✅ Collection '{PERSISTENT_COLLECTION}' is ready")
        except Exception as e:
            logger.error(f"❌ Failed to setup collection: {e}")
            raise
    
    async def check_existing_content(self) -> int:
        """Check how many documents are already in the collection."""
        try:
            info = await self.vector_store.get_collection_info(PERSISTENT_COLLECTION)
            point_count = info.get('points_count', 0)
            logger.info(f"📊 Collection '{PERSISTENT_COLLECTION}' currently has {point_count} points")
            return point_count
        except Exception as e:
            logger.warning(f"Could not check existing content: {e}")
            return 0
    
    async def ingest_document(self, document_path: str) -> bool:
        """Ingest a single document."""
        try:
            if not os.path.exists(document_path):
                logger.error(f"❌ Document not found: {document_path}")
                return False
            
            logger.info(f"🔄 Processing: {document_path}")
            
            # Process the document
            result = await self.worker.process_document(
                file_path=Path(document_path),
                collection_name=PERSISTENT_COLLECTION,
                metadata={"source": "manual_ingestion", "file_name": Path(document_path).name}
            )
            
            if result.get('success'):
                logger.info(f"✅ Successfully processed: {document_path}")
                logger.info(f"   - Chunks created: {result.get('chunks_created', 0)}")
                logger.info(f"   - Vectors stored: {result.get('vectors_stored', 0)}")
                return True
            else:
                logger.error(f"❌ Failed to process: {document_path}")
                logger.error(f"   - Error: {result.get('error', 'Unknown error')}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Exception processing {document_path}: {e}")
            return False
    
    async def ingest_all_documents(self, document_paths: List[str]) -> dict:
        """Ingest all specified documents."""
        results = {
            'total': len(document_paths),
            'successful': 0,
            'failed': 0,
            'failed_documents': []
        }
        
        for doc_path in document_paths:
            success = await self.ingest_document(doc_path)
            if success:
                results['successful'] += 1
            else:
                results['failed'] += 1
                results['failed_documents'].append(doc_path)
        
        return results
    
    async def get_collection_stats(self) -> dict:
        """Get statistics about the collection."""
        try:
            info = await self.vector_store.get_collection_info(PERSISTENT_COLLECTION)
            return {
                'collection_name': PERSISTENT_COLLECTION,
                'points_count': info.get('points_count', 0),
                'vector_size': info.get('config', {}).get('params', {}).get('vectors', {}).get('size', 0),
                'status': info.get('status', 'unknown')
            }
        except Exception as e:
            logger.error(f"Failed to get collection stats: {e}")
            return {}

async def main():
    """Main ingestion function."""
    print("🚀 Manual Testing Document Ingestion")
    print("=" * 50)
    
    # Check environment
    if not OPENAI_API_KEY:
        print("❌ OPENAI_API_KEY not found in environment")
        print("   Please set it in .env.local or .env file")
        return
    
    # Initialize service
    service = ManualIngestionService()
    
    try:
        # Setup collection
        await service.setup_collection()
        
        # Check existing content
        existing_points = await service.check_existing_content()
        
        if existing_points > 0:
            print(f"\n📊 Collection '{PERSISTENT_COLLECTION}' already has {existing_points} points")
            response = input("Do you want to add more documents? (y/N): ").strip().lower()
            if response != 'y':
                print("👋 Skipping ingestion. Collection is ready for manual testing.")
                stats = await service.get_collection_stats()
                print(f"\n📈 Collection Stats:")
                print(f"   - Name: {stats.get('collection_name', 'N/A')}")
                print(f"   - Points: {stats.get('points_count', 0)}")
                print(f"   - Vector Size: {stats.get('vector_size', 0)}")
                print(f"   - Status: {stats.get('status', 'unknown')}")
                return
        
        # Process documents
        print(f"\n🔄 Processing {len(TEST_DOCUMENTS)} documents...")
        results = await service.ingest_all_documents(TEST_DOCUMENTS)
        
        # Show results
        print(f"\n📊 Ingestion Results:")
        print(f"   - Total documents: {results['total']}")
        print(f"   - Successful: {results['successful']}")
        print(f"   - Failed: {results['failed']}")
        
        if results['failed_documents']:
            print(f"\n❌ Failed documents:")
            for doc in results['failed_documents']:
                print(f"   - {doc}")
        
        # Final stats
        stats = await service.get_collection_stats()
        print(f"\n📈 Final Collection Stats:")
        print(f"   - Name: {stats.get('collection_name', 'N/A')}")
        print(f"   - Points: {stats.get('points_count', 0)}")
        print(f"   - Vector Size: {stats.get('vector_size', 0)}")
        print(f"   - Status: {stats.get('status', 'unknown')}")
        
        print(f"\n✅ Ingestion complete! Collection '{PERSISTENT_COLLECTION}' is ready for manual RAG testing.")
        print(f"   Use this collection name in your manual RAG tests.")
        
    except Exception as e:
        logger.error(f"❌ Ingestion failed: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())
