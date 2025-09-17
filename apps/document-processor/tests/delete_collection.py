#!/usr/bin/env python3
"""
Script to delete the manual testing collection.
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

from rag.vector_store import VectorStore

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
COLLECTION_NAME = "manual_testing_kb"
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6336")

async def delete_collection():
    """Delete the manual testing collection."""
    print("🗑️  Collection Deletion Tool")
    print("=" * 30)
    
    vector_store = VectorStore(qdrant_url=QDRANT_URL)
    
    try:
        # Check if collection exists
        info = await vector_store.get_collection_info(COLLECTION_NAME)
        point_count = info.get('points_count', 0)
        print(f"📊 Collection '{COLLECTION_NAME}' has {point_count} points")
        
        # Confirm deletion
        response = input(f"\n⚠️  Are you sure you want to delete '{COLLECTION_NAME}'? (y/N): ").strip().lower()
        if response not in ['y', 'yes']:
            print("👋 Deletion cancelled.")
            return
        
        # Delete collection
        await vector_store.delete_collection(COLLECTION_NAME)
        print(f"✅ Successfully deleted collection '{COLLECTION_NAME}'")
        
    except Exception as e:
        if "not found" in str(e).lower():
            print(f"ℹ️  Collection '{COLLECTION_NAME}' doesn't exist")
        else:
            print(f"❌ Error deleting collection: {e}")

if __name__ == "__main__":
    asyncio.run(delete_collection())
