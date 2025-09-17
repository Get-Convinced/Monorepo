#!/usr/bin/env python3
"""
Simple script to run manual RAG testing with persistent collection.
This script will:
1. Check if the persistent collection exists and has content
2. If not, run the ingestion script
3. Then run manual RAG tests
"""

import asyncio
import subprocess
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

async def check_collection_status():
    """Check if the persistent collection exists and has content."""
    try:
        vector_store = VectorStore(qdrant_url="http://localhost:6336")
        info = await vector_store.get_collection_info("manual_testing_kb")
        point_count = info.get('points_count', 0)
        return point_count > 0
    except Exception:
        return False

async def main():
    """Main function to run manual RAG testing."""
    print("🚀 Manual RAG Testing Setup")
    print("=" * 40)
    
    # Check if collection has content
    has_content = await check_collection_status()
    
    if not has_content:
        print("📄 Collection 'manual_testing_kb' is empty or doesn't exist.")
        print("🔄 Running ingestion script...")
        
        try:
            # Run the ingestion script
            result = subprocess.run([
                sys.executable, "tests/ingest_for_manual_testing.py"
            ], check=True, capture_output=True, text=True)
            
            print("✅ Ingestion completed successfully!")
            print(result.stdout)
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Ingestion failed: {e}")
            print(f"Error output: {e.stderr}")
            return
    else:
        print("✅ Collection 'manual_testing_kb' already has content.")
    
    print("\n🎯 Starting manual RAG tests...")
    
    try:
        # Run the manual RAG tests
        result = subprocess.run([
            sys.executable, "tests/manual_rag_tests.py"
        ], check=True)
        
        print("✅ Manual RAG tests completed!")
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Manual RAG tests failed: {e}")
        return

if __name__ == "__main__":
    asyncio.run(main())
