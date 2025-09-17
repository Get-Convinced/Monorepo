"""
Search service for querying the knowledge base.
"""

import logging
from typing import List, Dict, Any, Optional
try:
    from .vector_store import VectorStore
    from ..embeddings import EmbeddingService
except ImportError:
    # Fallback for when running as script
    from rag.vector_store import VectorStore
    from embeddings import EmbeddingService

logger = logging.getLogger(__name__)


class SearchService:
    """Service for searching the knowledge base."""
    
    def __init__(self, vector_store: VectorStore, embedding_service: EmbeddingService):
        self.vector_store = vector_store
        self.embedding_service = embedding_service
    
    async def search(
        self, 
        query: str, 
        collection_name: str = "knowledge_base",
        limit: int = 5,
        score_threshold: float = 0.7,
        filter_conditions: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Search for relevant content."""
        try:
            # Generate query embedding
            query_embedding = await self.embedding_service.generate_embeddings([query])
            if not query_embedding:
                raise ValueError("Failed to generate query embedding")
            
            # Search in vector store
            results = await self.vector_store.search(
                collection_name=collection_name,
                query_vector=query_embedding[0],
                limit=limit,
                score_threshold=score_threshold,
                filter_conditions=filter_conditions
            )
            
            # Format results for API response
            formatted_results = []
            for result in results:
                payload = result["payload"]
                formatted_results.append({
                    "content": payload.get("content", ""),
                    "file_path": payload.get("file_path", ""),
                    "chunk_index": payload.get("chunk_index", 0),
                    "score": result["score"],
                    "metadata": {k: v for k, v in payload.items() 
                               if k not in ["content", "file_path", "chunk_index"]}
                })
            
            logger.info(f"Search query '{query}' returned {len(formatted_results)} results")
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error searching knowledge base: {e}")
            raise
    
    async def search_by_file(
        self, 
        file_path: str, 
        collection_name: str = "knowledge_base",
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Search for content from a specific file."""
        try:
            # Use filter to search only within specific file
            filter_conditions = {"file_path": file_path}
            
            # Get all chunks from the file (we'll use a dummy query vector)
            # In a real implementation, you might want to use a different approach
            dummy_query = "search all content"
            query_embedding = await self.embedding_service.generate_embeddings([dummy_query])
            
            results = await self.vector_store.search(
                collection_name=collection_name,
                query_vector=query_embedding[0],
                limit=limit,
                score_threshold=0.0,  # Low threshold to get all results
                filter_conditions=filter_conditions
            )
            
            # Format results
            formatted_results = []
            for result in results:
                payload = result["payload"]
                formatted_results.append({
                    "content": payload.get("content", ""),
                    "chunk_index": payload.get("chunk_index", 0),
                    "score": result["score"],
                    "metadata": {k: v for k, v in payload.items() 
                               if k not in ["content", "chunk_index"]}
                })
            
            logger.info(f"Found {len(formatted_results)} chunks from file {file_path}")
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error searching by file: {e}")
            raise
