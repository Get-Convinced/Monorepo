#!/usr/bin/env python3
"""
Quick ingestion script that processes only the first few pages for fast testing.
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

async def quick_ingest():
    """Quick ingestion of just a few pages for testing."""
    print("🚀 Quick Manual Testing Ingestion (First 3 pages only)")
    print("=" * 60)
    
    if not OPENAI_API_KEY:
        print("❌ OPENAI_API_KEY not found in environment")
        return
    
    # Initialize services
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
            response = input("Continue and add more? (y/N): ").strip().lower()
            if response != 'y':
                print("👋 Skipping ingestion.")
                return
    except Exception as e:
        logger.warning(f"Could not check collection: {e}")
    
    # Process just the first 3 pages of the PDF
    pdf_file = Path(__file__).parent / "test_data/Bizom _ Discussion Deck.pdf"
    if not pdf_file.exists():
        print(f"❌ Test file not found: {pdf_file}")
        return
    
    print(f"🔄 Processing first 3 pages of: {pdf_file.name}")
    
    try:
        # Create a temporary PDF with just first 3 pages
        import fitz  # PyMuPDF
        doc = fitz.open(str(pdf_file))
        
        # Create new document with first 3 pages
        new_doc = fitz.open()
        for page_num in range(min(3, len(doc))):
            new_doc.insert_pdf(doc, from_page=page_num, to_page=page_num)
        
        # Save temporary file
        temp_file = Path("temp_first_3_pages.pdf")
        new_doc.save(str(temp_file))
        new_doc.close()
        doc.close()
        
        print(f"📄 Created temporary file: {temp_file}")
        
        # Process the temporary file
        result = await worker.process_document(
            file_path=temp_file,
            collection_name=PERSISTENT_COLLECTION,
            metadata={
                "source": "quick_ingestion", 
                "file_name": pdf_file.name,
                "pages": "1-3"
            }
        )
        
        # Clean up temporary file
        temp_file.unlink()
        print(f"🧹 Cleaned up temporary file")
        
        if result.get('success'):
            print(f"✅ Successfully processed first 3 pages!")
            print(f"   - Chunks created: {result.get('chunks_created', 0)}")
            print(f"   - Vectors stored: {result.get('vectors_stored', 0)}")
            
            # Show final stats
            info = await vector_store.get_collection_info(PERSISTENT_COLLECTION)
            point_count = info.get('points_count', 0)
            print(f"📊 Collection now has {point_count} total points")
            print(f"✅ Ready for manual RAG testing!")
        else:
            print(f"❌ Processing failed: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        logger.error(f"❌ Quick ingestion failed: {e}")
        # Clean up temp file if it exists
        temp_file = Path("temp_first_3_pages.pdf")
        if temp_file.exists():
            temp_file.unlink()

if __name__ == "__main__":
    asyncio.run(quick_ingest())
