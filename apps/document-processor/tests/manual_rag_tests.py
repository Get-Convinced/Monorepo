"""
Manual RAG and Retrieval Tests
=============================

Interactive scripts for manual testing of RAG functionality:
- Qdrant retrieval testing
- RAG question-answering with GPT-4o
- Search quality evaluation
- End-to-end RAG workflow testing

These are manual tests that require user interaction and evaluation.
"""

import asyncio
import os
import sys
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

# Load environment variables from .env files
try:
    from dotenv import load_dotenv
    # Load from multiple possible .env files
    load_dotenv('.env.local')  # Local development
    load_dotenv('.env')        # General environment
    load_dotenv('.env.test')   # Test-specific environment
except ImportError:
    pass  # python-dotenv not available

# Add src to path
SRC_DIR = Path(__file__).parents[1] / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from embeddings import EmbeddingService
from rag.vector_store import VectorStore
from rag.search_service import SearchService
from rag.rag_service import RAGService
from workers.unified_document_worker import UnifiedDocumentWorker
from processors.unified_document_processor import GPTModel

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuration
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6336")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
EMBED_MODEL = os.getenv("EMBED_MODEL", "mxbai-embed-large")
EMBED_DIMENSION = int(os.getenv("EMBED_DIMENSION", "1024"))
COLLECTION_NAME = os.getenv("COLLECTION", "manual_testing_kb")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GPT_MODEL = os.getenv("GPT_MODEL", "gpt-4o")


class ManualRAGTester:
    """Interactive RAG testing tool."""
    
    def __init__(self):
        """Initialize the RAG tester."""
        self.vector_store = None
        self.embedding_service = None
        self.rag_service = None
        self.collection_name = COLLECTION_NAME
        
    async def setup(self):
        """Setup services and collections."""
        logger.info("🔧 Setting up RAG testing environment...")
        
        # Initialize services
        self.vector_store = VectorStore(qdrant_url=QDRANT_URL)
        self.embedding_service = EmbeddingService.create_ollama_provider(
            base_url=OLLAMA_BASE_URL,
            model=EMBED_MODEL
        )
        
        if OPENAI_API_KEY:
            # Create search service first
            search_service = SearchService(
                vector_store=self.vector_store,
                embedding_service=self.embedding_service
            )
            # Then create RAG service
            self.rag_service = RAGService(search_service=search_service)
        
        # Check if collection exists and has content
        try:
            info = await self.vector_store.get_collection_info(self.collection_name)
            point_count = info.get('points_count', 0)
            if point_count == 0:
                logger.warning(f"⚠️  Collection '{self.collection_name}' exists but is empty!")
                logger.info("💡 Run 'python ingest_for_manual_testing.py' to populate it with documents.")
                return False
            else:
                logger.info(f"✅ Collection '{self.collection_name}' has {point_count} points ready for testing")
        except Exception as e:
            logger.error(f"❌ Collection '{self.collection_name}' not found or error: {e}")
            logger.info("💡 Run 'python ingest_for_manual_testing.py' to create and populate the collection.")
            return False
        
        logger.info(f"✅ Setup complete. Collection: {self.collection_name}")
        return True
    
    async def ingest_documents(self, file_paths: List[Path]):
        """Ingest documents into the vector store."""
        if not OPENAI_API_KEY:
            logger.error("❌ OPENAI_API_KEY not set. Cannot ingest documents.")
            return
        
        logger.info(f"📄 Ingesting {len(file_paths)} documents...")
        
        # Initialize document worker
        gpt_model = GPTModel(GPT_MODEL)
        worker = UnifiedDocumentWorker(
            embedding_service=self.embedding_service,
            vector_store=self.vector_store,
            openai_api_key=OPENAI_API_KEY,
            gpt_model=gpt_model
        )
        
        # Process documents
        result = await worker.process_multiple_documents(
            file_paths=file_paths,
            collection_name=self.collection_name,
            metadata={
                "test_type": "manual_rag",
                "timestamp": "2024-01-01T00:00:00Z"
            }
        )
        
        logger.info(f"✅ Ingestion complete:")
        logger.info(f"   Documents: {result['total_documents']}")
        logger.info(f"   Successful: {result['successful']}")
        logger.info(f"   Failed: {result['failed']}")
        logger.info(f"   Chunks: {result['total_chunks']}")
        logger.info(f"   Vectors: {result['total_points']}")
        
        return result
    
    async def test_vector_search(self, query: str, limit: int = 5):
        """Test vector search functionality."""
        logger.info(f"🔍 Testing vector search for: '{query}'")
        
        # Generate query embedding
        query_embedding = await self.embedding_service.embed_text(query)
        
        # Search vectors
        results = await self.vector_store.search(
            collection_name=self.collection_name,
            query_vector=query_embedding,
            limit=limit
        )
        
        logger.info(f"📊 Found {len(results)} results:")
        for i, result in enumerate(results, 1):
            text = result["payload"]["text"][:200] + "..." if len(result["payload"]["text"]) > 200 else result["payload"]["text"]
            logger.info(f"   {i}. Score: {result['score']:.3f}")
            logger.info(f"      Text: {text}")
            logger.info(f"      Metadata: {result['payload'].get('metadata', {})}")
            logger.info("")
        
        return results
    
    async def test_rag_question_answering(self, question: str, max_context_chunks: int = 5):
        """Test RAG question answering."""
        if not self.rag_service:
            logger.error("❌ RAG service not available. Need OPENAI_API_KEY.")
            return None
        
        logger.info(f"🤖 Testing RAG Q&A for: '{question}'")
        
        # Get answer from RAG service
        answer = await self.rag_service.ask_question(
            question=question,
            collection_name=self.collection_name,
            max_context_chunks=max_context_chunks
        )
        
        logger.info(f"💡 Answer: {answer['answer']}")
        logger.info(f"📚 Context chunks used: {len(answer.get('context_chunks', []))}")
        logger.info(f"🔍 Sources: {len(answer.get('sources', []))}")
        
        # Show context chunks
        if answer.get('context_chunks'):
            logger.info("\n📖 Context chunks:")
            for i, chunk in enumerate(answer['context_chunks'][:3], 1):  # Show first 3
                text = chunk['text'][:150] + "..." if len(chunk['text']) > 150 else chunk['text']
                logger.info(f"   {i}. {text}")
        
        return answer
    
    async def interactive_search_test(self):
        """Interactive search testing session."""
        logger.info("🎯 Starting interactive search test...")
        logger.info("Type 'quit' to exit, 'help' for commands")
        
        while True:
            try:
                query = input("\n🔍 Enter search query: ").strip()
                
                if query.lower() == 'quit':
                    break
                elif query.lower() == 'help':
                    print("Commands:")
                    print("  quit - Exit the test")
                    print("  help - Show this help")
                    print("  stats - Show collection statistics")
                    print("  <query> - Search for the query")
                elif query.lower() == 'stats':
                    await self.show_collection_stats()
                elif query:
                    await self.test_vector_search(query)
                else:
                    print("Please enter a query or command.")
                    
            except KeyboardInterrupt:
                break
            except Exception as e:
                logger.error(f"Error: {e}")
        
        logger.info("👋 Interactive search test ended.")
    
    async def interactive_rag_test(self):
        """Interactive RAG testing session."""
        if not self.rag_service:
            logger.error("❌ RAG service not available. Need OPENAI_API_KEY.")
            return
        
        logger.info("🤖 Starting interactive RAG test...")
        logger.info("Type 'quit' to exit, 'help' for commands")
        
        while True:
            try:
                question = input("\n❓ Enter your question: ").strip()
                
                if question.lower() == 'quit':
                    break
                elif question.lower() == 'help':
                    print("Commands:")
                    print("  quit - Exit the test")
                    print("  help - Show this help")
                    print("  stats - Show collection statistics")
                    print("  <question> - Ask a question")
                elif question.lower() == 'stats':
                    await self.show_collection_stats()
                elif question:
                    await self.test_rag_question_answering(question)
                else:
                    print("Please enter a question or command.")
                    
            except KeyboardInterrupt:
                break
            except Exception as e:
                logger.error(f"Error: {e}")
        
        logger.info("👋 Interactive RAG test ended.")
    
    async def show_collection_stats(self):
        """Show collection statistics."""
        try:
            info = await self.vector_store.get_collection_info(self.collection_name)
            logger.info(f"📊 Collection Statistics:")
            logger.info(f"   Name: {self.collection_name}")
            logger.info(f"   Points: {info.get('points_count', 0)}")
            logger.info(f"   Vectors: {info.get('vectors_count', 0)}")
        except Exception as e:
            logger.error(f"Failed to get collection stats: {e}")
    
    async def cleanup(self):
        """Cleanup test collections."""
        try:
            await self.vector_store.delete_collection(self.collection_name)
            logger.info(f"🧹 Cleaned up collection: {self.collection_name}")
        except Exception as e:
            logger.warning(f"Failed to cleanup collection: {e}")


async def run_manual_tests():
    """Run manual RAG tests."""
    tester = ManualRAGTester()
    
    try:
        setup_success = await tester.setup()
        if not setup_success:
            print("❌ Setup failed. Please run the ingestion script first.")
            return
        
        # Get test files
        test_data_dir = Path(__file__).parent / "test_data"
        test_files = [
            test_data_dir / "Bizom _ Discussion Deck.pdf",
            test_data_dir / "Bizom _ Omnichannel_Celesta.pdf",
            test_data_dir / "Bizom _ Pitch Deck_Full Deck_UI Updated.pdf"
        ]
        
        existing_files = [f for f in test_files if f.exists()]
        
        if not existing_files:
            logger.error("❌ No test files found. Please add PDF files to tests/test_data/")
            return
        
        logger.info(f"📁 Found {len(existing_files)} test files:")
        for file_path in existing_files:
            logger.info(f"   - {file_path.name}")
        
        # Ask user what to do
        print("\n🎯 Manual RAG Testing Options:")
        print("1. Ingest documents and run interactive search")
        print("2. Ingest documents and run interactive RAG Q&A")
        print("3. Just run interactive search (assumes documents already ingested)")
        print("4. Just run interactive RAG Q&A (assumes documents already ingested)")
        print("5. Show collection statistics")
        print("6. Exit")
        
        while True:
            try:
                choice = input("\nSelect option (1-6): ").strip()
                
                if choice == "1":
                    await tester.ingest_documents(existing_files)
                    await tester.interactive_search_test()
                    break
                elif choice == "2":
                    await tester.ingest_documents(existing_files)
                    await tester.interactive_rag_test()
                    break
                elif choice == "3":
                    await tester.interactive_search_test()
                    break
                elif choice == "4":
                    await tester.interactive_rag_test()
                    break
                elif choice == "5":
                    await tester.show_collection_stats()
                elif choice == "6":
                    break
                else:
                    print("Please select a valid option (1-6).")
                    
            except KeyboardInterrupt:
                break
            except Exception as e:
                logger.error(f"Error: {e}")
    
    finally:
        # Ask if user wants to cleanup
        try:
            cleanup = input("\n🧹 Cleanup test collection? (y/N): ").strip().lower()
            if cleanup in ['y', 'yes']:
                await tester.cleanup()
        except KeyboardInterrupt:
            pass


async def run_predefined_tests():
    """Run predefined test scenarios."""
    tester = ManualRAGTester()
    
    try:
        setup_success = await tester.setup()
        if not setup_success:
            print("❌ Setup failed. Please run the ingestion script first.")
            return
        
        # Get test files
        test_data_dir = Path(__file__).parent / "test_data"
        test_files = [
            test_data_dir / "Bizom _ Discussion Deck.pdf",
            test_data_dir / "Bizom _ Omnichannel_Celesta.pdf",
            test_data_dir / "Bizom _ Pitch Deck_Full Deck_UI Updated.pdf"
        ]
        
        existing_files = [f for f in test_files if f.exists()]
        
        if not existing_files:
            logger.error("❌ No test files found.")
            return
        
        # Ingest documents
        logger.info("📄 Ingesting documents for predefined tests...")
        await tester.ingest_documents(existing_files)
        
        # Predefined test queries
        test_queries = [
            "What is Bizom?",
            "What are the key features of Bizom?",
            "How does Bizom handle omnichannel?",
            "What is the business model of Bizom?",
            "What are the technical capabilities?",
            "What is the market opportunity?",
            "Who are the competitors?",
            "What is the revenue model?"
        ]
        
        logger.info("🎯 Running predefined test queries...")
        
        for i, query in enumerate(test_queries, 1):
            logger.info(f"\n{'='*60}")
            logger.info(f"Test {i}/{len(test_queries)}: {query}")
            logger.info(f"{'='*60}")
            
            # Test vector search
            await tester.test_vector_search(query, limit=3)
            
            # Test RAG if available
            if tester.rag_service:
                await tester.test_rag_question_answering(query, max_context_chunks=3)
            
            # Pause between tests
            if i < len(test_queries):
                input("\nPress Enter to continue to next test...")
        
        logger.info("\n🎉 Predefined tests completed!")
        
    finally:
        # Ask if user wants to cleanup
        try:
            cleanup = input("\n🧹 Cleanup test collection? (y/N): ").strip().lower()
            if cleanup in ['y', 'yes']:
                await tester.cleanup()
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    print("🚀 Manual RAG Testing Tool")
    print("=" * 50)
    
    if not OPENAI_API_KEY:
        print("⚠️  Warning: OPENAI_API_KEY not set. RAG Q&A features will not be available.")
        print("   Set OPENAI_API_KEY environment variable to enable RAG testing.")
    
    print("\nOptions:")
    print("1. Interactive testing")
    print("2. Predefined test scenarios")
    
    try:
        choice = input("\nSelect option (1-2): ").strip()
        
        if choice == "1":
            asyncio.run(run_manual_tests())
        elif choice == "2":
            asyncio.run(run_predefined_tests())
        else:
            print("Invalid choice. Exiting.")
            
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        logger.error(f"Error: {e}")
