#!/usr/bin/env python3
"""
Full document ingestion script for manual RAG testing.
This processes ALL pages of the PDF documents.
"""

import asyncio
import logging
import os
import sys
from pathlib import Path

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
PERSISTENT_COLLECTION = "manual_testing_kb"
EMBED_DIMENSION = 1024
EMBED_MODEL = "mxbai-embed-large"
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6336")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GPT_MODEL = GPTModel.GPT_4O_MINI

# All test documents to process
TEST_DOCUMENTS = [
    "test_data/Bizom _ Discussion Deck.pdf",
    "test_data/Bizom _ Omnichannel_Celesta.pdf", 
    "test_data/Bizom _ Pitch Deck_Full Deck_UI Updated.pdf"
]

async def full_ingest():
    """Full ingestion of all documents."""
    print("🚀 Full Document Ingestion for Manual RAG Testing")
    print("=" * 60)
    
    if not OPENAI_API_KEY:
        print("❌ OPENAI_API_KEY not found in environment")
        return
    
    # Initialize services (same as quick_ingest.py)
    vector_store = VectorStore(qdrant_url=QDRANT_URL)
    embedding_service = EmbeddingService.create_ollama_provider(
        base_url=OLLAMA_BASE_URL,
        model=EMBED_MODEL
    )
    worker = UnifiedDocumentWorker(
        embedding_service=embedding_service,
        vector_store=vector_store,
        openai_api_key=OPENAI_API_KEY,
        gpt_model=GPT_MODEL
    )
    
    # Setup collection
    await vector_store.ensure_collection_exists(PERSISTENT_COLLECTION, EMBED_DIMENSION)
    logger.info(f"✅ Collection '{PERSISTENT_COLLECTION}' ready")
    
    # Check existing content
    try:
        info = await vector_store.get_collection_info(PERSISTENT_COLLECTION)
        point_count = info.get('points_count', 0)
        if point_count > 0:
            print(f"📊 Collection already has {point_count} points")
            response = input("Continue and add more documents? (y/N): ").strip().lower()
            if response != 'y':
                print("👋 Skipping ingestion.")
                return
    except Exception as e:
        logger.warning(f"Could not check collection: {e}")
    
    # Process all documents
    results = {
        'total': 0,
        'successful': 0,
        'failed': 0,
        'failed_documents': []
    }
    
    for doc_path in TEST_DOCUMENTS:
        full_path = Path(__file__).parent / doc_path
        if not full_path.exists():
            print(f"⚠️  Document not found: {doc_path}")
            results['failed'] += 1
            results['failed_documents'].append(doc_path)
            continue
        
        results['total'] += 1
        print(f"\n🔄 Processing: {full_path.name}")
        
        try:
            # Process document using the same approach as quick_ingest.py
            result = await worker.process_document(
                file_path=full_path,
                collection_name=PERSISTENT_COLLECTION,
                metadata={
                    "source": "full_ingestion", 
                    "file_name": full_path.name
                }
            )
            
            if result.get('success'):
                print(f"✅ Successfully processed: {full_path.name}")
                print(f"   - Chunks created: {result.get('chunks_created', 0)}")
                print(f"   - Vectors stored: {result.get('vectors_stored', 0)}")
                results['successful'] += 1
            else:
                print(f"❌ Failed to process: {full_path.name}")
                print(f"   - Error: {result.get('error', 'Unknown error')}")
                results['failed'] += 1
                results['failed_documents'].append(doc_path)
                
        except Exception as e:
            print(f"❌ Exception processing {full_path.name}: {e}")
            results['failed'] += 1
            results['failed_documents'].append(doc_path)
    
    # Show final results
    print(f"\n📊 Full Ingestion Results:")
    print(f"   - Total documents: {results['total']}")
    print(f"   - Successful: {results['successful']}")
    print(f"   - Failed: {results['failed']}")
    
    if results['failed_documents']:
        print(f"\n❌ Failed documents:")
        for doc in results['failed_documents']:
            print(f"   - {doc}")
    
    # Final stats
    try:
        info = await vector_store.get_collection_info(PERSISTENT_COLLECTION)
        point_count = info.get('points_count', 0)
        print(f"\n📈 Final Collection Stats:")
        print(f"   - Collection: {PERSISTENT_COLLECTION}")
        print(f"   - Total points: {point_count}")
        print(f"   - Status: {info.get('status', 'unknown')}")
        print(f"\n✅ Full ingestion complete! Ready for comprehensive RAG testing.")
    except Exception as e:
        print(f"❌ Could not get final stats: {e}")

if __name__ == "__main__":
    asyncio.run(full_ingest())
