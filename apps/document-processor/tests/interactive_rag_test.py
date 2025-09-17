#!/usr/bin/env python3
"""
Interactive RAG Test - Ask questions and get RAG-powered answers
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
from rag.search_service import SearchService
from rag.rag_service import RAGService
from embeddings import EmbeddingService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
COLLECTION_NAME = "manual_testing_kb"
EMBED_DIMENSION = 1024
EMBED_MODEL = "mxbai-embed-large"
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6336")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

async def generate_answer_with_gpt(question: str, context: str) -> str:
    """Generate an answer using GPT-4o-mini based on the question and context."""
    try:
        import openai
        
        if not OPENAI_API_KEY:
            return "❌ I cannot generate an answer because no OpenAI API key is configured."
        
        client = openai.OpenAI(api_key=OPENAI_API_KEY)
        
        prompt = f"""Based on the following context from Bizom's documents, please answer the question. If the context doesn't contain enough information to answer the question, say so.

Question: {question}

Context:
{context}

Please provide a clear, helpful answer based on the available information:"""
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "user", "content": prompt}
            ],
            max_tokens=800,
            temperature=0.1
        )
        
        return response.choices[0].message.content.strip()
        
    except Exception as e:
        logger.error(f"Error generating answer: {e}")
        return f"❌ I encountered an error while generating an answer: {str(e)}"

async def interactive_rag():
    """Interactive RAG testing session."""
    print("🚀 Interactive RAG Test")
    print("=" * 50)
    print("Ask questions about Bizom's business, metrics, customers, and more!")
    print("Type 'quit', 'exit', or 'q' to end the session.")
    print("=" * 50)
    
    if not OPENAI_API_KEY:
        print("❌ OPENAI_API_KEY not found in environment")
        return
    
    # Initialize services
    vector_store = VectorStore(qdrant_url=QDRANT_URL)
    embedding_service = EmbeddingService.create_ollama_provider(
        base_url=OLLAMA_BASE_URL,
        model=EMBED_MODEL
    )
    search_service = SearchService(
        vector_store=vector_store,
        embedding_service=embedding_service
    )
    rag_service = RAGService(search_service=search_service)
    
    # Check collection status
    try:
        info = await vector_store.get_collection_info(COLLECTION_NAME)
        point_count = info.get('points_count', 0)
        print(f"📊 Collection '{COLLECTION_NAME}' has {point_count} points")
        
        if point_count == 0:
            print("❌ Collection is empty. Run quick_ingest.py or full_ingest.py first.")
            return
            
    except Exception as e:
        print(f"❌ Collection error: {e}")
        return
    
    print(f"\n✅ Ready! You can ask questions about:")
    print("   • Bizom's business model and services")
    print("   • Financial metrics and growth")
    print("   • Customer success stories")
    print("   • Market expansion and strategy")
    print("   • Technology and platform features")
    print("   • Competition and positioning")
    print()
    
    # Interactive loop
    while True:
        try:
            # Get user input
            question = input("\n🤔 Your question: ").strip()
            
            # Check for exit commands
            if question.lower() in ['quit', 'exit', 'q', '']:
                print("\n👋 Goodbye! Thanks for testing the RAG system!")
                break
            
            print(f"\n🔍 Searching for relevant information...")
            
            # Search for relevant content
            search_results = await search_service.search(
                query=question,
                collection_name=COLLECTION_NAME,
                limit=5,
                score_threshold=0.3
            )
            
            if not search_results:
                print("❌ No relevant information found for your question.")
                continue
            
            print(f"✅ Found {len(search_results)} relevant chunks")
            
            # Get RAG context
            rag_result = await rag_service.ask_question(
                question=question,
                collection_name=COLLECTION_NAME,
                max_context_chunks=5,
                score_threshold=0.3
            )
            
            if not rag_result.get('context_found'):
                print("❌ Could not find relevant context for your question.")
                continue
            
            print(f"📚 Retrieved context (confidence: {rag_result.get('confidence', 0):.3f})")
            print(f"🤖 Generating answer with GPT-4o-mini...")
            
            # Generate answer
            answer = await generate_answer_with_gpt(question, rag_result.get('context', ''))
            
            print(f"\n💡 Answer:")
            print("-" * 50)
            print(answer)
            print("-" * 50)
            
            # Show sources
            sources = rag_result.get('sources', [])
            if sources:
                print(f"\n📖 Sources ({len(sources)}):")
                for i, source in enumerate(sources[:3], 1):  # Show top 3 sources
                    file_name = source.get('file_path', 'Unknown').split('/')[-1]
                    score = source.get('score', 0)
                    print(f"   {i}. {file_name} (score: {score:.3f})")
            
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye! Thanks for testing the RAG system!")
            break
        except Exception as e:
            print(f"\n❌ Error processing question: {e}")
            logger.error(f"Error in interactive session: {e}")

if __name__ == "__main__":
    asyncio.run(interactive_rag())
