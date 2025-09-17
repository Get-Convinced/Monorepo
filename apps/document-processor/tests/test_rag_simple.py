#!/usr/bin/env python3
"""
Simple RAG test script that runs automatically without user input.
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
    """Generate an answer using GPT based on the question and context."""
    try:
        import openai
        
        if not OPENAI_API_KEY:
            return "I cannot generate an answer because no OpenAI API key is configured."
        
        client = openai.OpenAI(api_key=OPENAI_API_KEY)
        
        prompt = f"""Based on the following context, please answer the question. If the context doesn't contain enough information to answer the question, say so.

Question: {question}

Context:
{context}

Answer:"""
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "user", "content": prompt}
            ],
            max_tokens=500,
            temperature=0.1
        )
        
        return response.choices[0].message.content.strip()
        
    except Exception as e:
        logger.error(f"Error generating answer: {e}")
        return f"I encountered an error while generating an answer: {str(e)}"

async def test_rag():
    """Test RAG functionality with the ingested content."""
    print("🚀 Simple RAG Test")
    print("=" * 30)
    
    if not OPENAI_API_KEY:
        print("❌ OPENAI_API_KEY not found")
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
            print("❌ Collection is empty. Run quick_ingest.py first.")
            return
            
    except Exception as e:
        print(f"❌ Collection error: {e}")
        return
    
    # Test queries
    test_queries = [
        "What is Bizom?",
        "What are the key features?",
        "What is the business model?",
        "Tell me about the company",
        "What services does Bizom provide?"
    ]
    
    print(f"\n🎯 Testing {len(test_queries)} queries...")
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n{'='*50}")
        print(f"Query {i}: {query}")
        print(f"{'='*50}")
        
        try:
            # Test vector search first
            print("🔍 Testing vector search...")
            search_results = await search_service.search(
                query=query,
                collection_name=COLLECTION_NAME,
                limit=3,
                score_threshold=0.3  # Lower threshold for testing
            )
            
            if search_results:
                print(f"✅ Found {len(search_results)} relevant chunks:")
                for j, result in enumerate(search_results, 1):
                    print(f"   {j}. Score: {result.get('score', 0):.3f}")
                    content = result.get('content', '')[:100] + "..." if len(result.get('content', '')) > 100 else result.get('content', '')
                    print(f"      Content: {content}")
            else:
                print("❌ No relevant chunks found")
            
            # Test RAG if we have search results
            if search_results:
                print("\n🤖 Testing RAG Q&A...")
                rag_result = await rag_service.ask_question(
                    question=query,
                    collection_name=COLLECTION_NAME,
                    max_context_chunks=3,
                    score_threshold=0.3
                )
                
                if rag_result.get('context_found'):
                    # Generate answer using GPT
                    answer = await generate_answer_with_gpt(query, rag_result.get('context', ''))
                    print(f"✅ RAG Answer: {answer}")
                    print(f"   Confidence: {rag_result.get('confidence', 0):.3f}")
                    print(f"   Sources: {len(rag_result.get('sources', []))}")
                else:
                    print("❌ RAG couldn't find relevant context")
            else:
                print("⏭️  Skipping RAG test (no search results)")
                
        except Exception as e:
            print(f"❌ Error testing query: {e}")
    
    print(f"\n🎉 RAG testing completed!")

if __name__ == "__main__":
    asyncio.run(test_rag())
