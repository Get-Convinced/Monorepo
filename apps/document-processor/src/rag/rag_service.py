"""
RAG service for question answering with retrieved context.
"""

import logging
from typing import List, Dict, Any, Optional
try:
    from .search_service import SearchService
except ImportError:
    # Fallback for when running as script
    from rag.search_service import SearchService

logger = logging.getLogger(__name__)


class RAGService:
    """RAG service for question answering."""
    
    def __init__(self, search_service: SearchService):
        self.search_service = search_service
    
    async def ask_question(
        self, 
        question: str, 
        collection_name: str = "knowledge_base",
        max_context_chunks: int = 3,
        score_threshold: float = 0.7
    ) -> Dict[str, Any]:
        """Ask a question and get relevant context."""
        try:
            # Search for relevant content
            search_results = await self.search_service.search(
                query=question,
                collection_name=collection_name,
                limit=max_context_chunks,
                score_threshold=score_threshold
            )
            
            if not search_results:
                return {
                    "question": question,
                    "answer": "I couldn't find any relevant information to answer your question.",
                    "sources": [],
                    "context_found": False,
                    "confidence": 0.0
                }
            
            # Combine context from top results
            context_chunks = []
            sources = []
            
            for result in search_results:
                context_chunks.append(result["content"])
                sources.append({
                    "file_path": result["file_path"],
                    "chunk_index": result["chunk_index"],
                    "score": result["score"],
                    "metadata": result["metadata"]
                })
            
            context = "\n\n".join(context_chunks)
            
            # Calculate average confidence
            avg_confidence = sum(r["score"] for r in search_results) / len(search_results)
            
            # Return the retrieved context (LLM answer generation handled by caller)
            return {
                "question": question,
                "context": context,
                "sources": sources,
                "context_found": True,
                "confidence": avg_confidence
            }
            
        except Exception as e:
            logger.error(f"Error processing question: {e}")
            raise
    
    async def get_document_summary(
        self, 
        file_path: str, 
        collection_name: str = "knowledge_base"
    ) -> Dict[str, Any]:
        """Get a summary of a document by retrieving its chunks."""
        try:
            # Get all chunks from the document
            chunks = await self.search_service.search_by_file(
                file_path=file_path,
                collection_name=collection_name
            )
            
            if not chunks:
                return {
                    "file_path": file_path,
                    "summary": "No content found for this document.",
                    "chunk_count": 0,
                    "total_characters": 0
                }
            
            # Combine all chunks
            full_content = "\n".join(chunk["content"] for chunk in chunks)
            
            # Basic statistics
            total_chars = len(full_content)
            chunk_count = len(chunks)
            
            # Simple summary (first 500 characters)
            summary = full_content[:500] + "..." if len(full_content) > 500 else full_content
            
            return {
                "file_path": file_path,
                "summary": summary,
                "chunk_count": chunk_count,
                "total_characters": total_chars,
                "chunks": chunks
            }
            
        except Exception as e:
            logger.error(f"Error getting document summary: {e}")
            raise
