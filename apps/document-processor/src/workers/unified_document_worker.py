"""
Unified Document Worker
======================

Handles document processing, embedding generation, and vector storage.
Uses the UnifiedDocumentProcessor to route files to appropriate processors.
All outputs are embedded via mxbai and stored in Qdrant.
"""

import logging
import uuid
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

from embeddings import EmbeddingService
from rag.vector_store import VectorStore
from processors.unified_document_processor import UnifiedDocumentProcessor, GPTModel
from processors.docling_chunker import DoclingChunker

logger = logging.getLogger(__name__)


class UnifiedDocumentWorker:
    """
    Unified worker that processes documents and stores them in vector database.
    
    Workflow:
    1. Route document to appropriate processor (GPT for PDF/PPT, Docling for others)
    2. Generate embeddings using mxbai
    3. Store in Qdrant vector database
    """
    
    def __init__(
        self,
        embedding_service: EmbeddingService,
        vector_store: VectorStore,
        openai_api_key: str,
        gpt_model: GPTModel = GPTModel.GPT_4O,
        text_chunk_size: int = 1000,
        text_chunk_overlap: int = 200,
        visual_extraction_dpi: int = 600,
        **processor_kwargs
    ):
        """
        Initialize unified document worker.
        
        Args:
            embedding_service: Service for generating embeddings
            vector_store: Vector database for storage
            openai_api_key: OpenAI API key for GPT models
            gpt_model: GPT model to use for visual processing
            text_chunk_size: Size of text chunks for Docling processing
            text_chunk_overlap: Overlap between text chunks
            visual_extraction_dpi: DPI for visual extraction
            **processor_kwargs: Additional processor configuration
        """
        self.embedding_service = embedding_service
        self.vector_store = vector_store
        
        # Initialize unified processor
        self.processor = UnifiedDocumentProcessor(
            openai_api_key=openai_api_key,
            gpt_model=gpt_model,
            visual_extraction_dpi=visual_extraction_dpi,
            **processor_kwargs
        )
        
        # Initialize chunker for Docling outputs
        self.chunker = DoclingChunker(
            text_chunk_size=text_chunk_size,
            text_chunk_overlap=text_chunk_overlap
        )
        
        logger.info(f"Initialized UnifiedDocumentWorker with GPT model: {gpt_model.value}")
    
    async def process_document(
        self,
        file_path: Path,
        collection_name: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process document and store in vector database.
        
        Args:
            file_path: Path to document file
            collection_name: Name of Qdrant collection
            metadata: Additional metadata to store
            
        Returns:
            Dictionary with processing results
        """
        if metadata is None:
            metadata = {}
        
        logger.info(f"Processing document: {file_path.name}")
        
        try:
            # Process document with unified processor
            result = await self.processor.process_document(file_path)
            
            # Prepare base metadata
            base_metadata = {
                "source": file_path.name,
                "file_path": str(file_path),
                "processor": result.get("processor", "unknown"),
                "file_type": result.get("file_type", "unknown"),
                "processing_method": result.get("processing_method", "unknown"),
                "created_at": datetime.utcnow().isoformat(),
                **metadata
            }
            
            # Handle different processing results
            if result.get("processor", "").startswith("gpt_"):
                # GPT processing - store full content as single chunk
                chunks = await self._create_gpt_chunks(result, base_metadata)
            else:
                # Docling processing - chunk the content
                chunks = await self._create_docling_chunks(result, base_metadata)
            
            if not chunks:
                logger.warning(f"No chunks created for {file_path.name}")
                return {
                    "success": False,
                    "error": "No chunks created",
                    "file_path": str(file_path)
                }
            
            # Generate embeddings and store in vector database
            points_to_upsert = []
            for chunk in chunks:
                try:
                    # Generate embedding
                    embedding = await self.embedding_service.generate_embeddings([chunk["content"]])
                    
                    # Create point for Qdrant
                    point = {
                        "id": str(uuid.uuid4()),
                        "vector": embedding[0],
                        "payload": {
                            "content": chunk["content"],
                            "chunk_type": chunk["chunk_type"],
                            "chunk_index": chunk["chunk_index"],
                            **chunk["metadata"]
                        }
                    }
                    points_to_upsert.append(point)
                    
                except Exception as e:
                    logger.error(f"Error generating embedding for chunk {chunk['chunk_index']}: {e}")
            
            if points_to_upsert:
                # Store in vector database
                await self.vector_store.upsert_points(collection_name, points_to_upsert)
                logger.info(f"Stored {len(points_to_upsert)} points in collection: {collection_name}")
            
            return {
                "success": True,
                "file_path": str(file_path),
                "processor": result.get("processor", "unknown"),
                "file_type": result.get("file_type", "unknown"),
                "chunks_created": len(chunks),
                "points_stored": len(points_to_upsert),
                "processing_method": result.get("processing_method", "unknown"),
                "metadata": base_metadata
            }
            
        except Exception as e:
            logger.error(f"Error processing document {file_path}: {e}")
            return {
                "success": False,
                "error": str(e),
                "file_path": str(file_path)
            }
    
    async def _create_gpt_chunks(
        self,
        result: Dict[str, Any],
        base_metadata: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Create chunks from GPT processing results."""
        content = result.get("content", "")
        if not content:
            return []
        
        # For GPT results, store as single chunk with full content
        chunk = {
            "content": content,
            "chunk_type": "gpt_visual_analysis",
            "chunk_index": 0,
            "metadata": {
                **base_metadata,
                "total_pages": result.get("total_pages", 1),
                "page_metadata": result.get("page_metadata", []),
                "token_usage": result.get("token_usage", 0),
                "model": result.get("model", "unknown")
            }
        }
        
        return [chunk]
    
    async def _create_docling_chunks(
        self,
        result: Dict[str, Any],
        base_metadata: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Create chunks from Docling processing results."""
        content = result.get("content", "")
        if not content:
            return []
        
        # Use Docling chunker to create multiple chunks
        docling_result = {
            "content": content,
            "metadata": result.get("metadata", {}),
            "structured_elements": result.get("structured_elements", {})
        }
        
        chunks = self.chunker.chunk_docling_result(docling_result)
        
        # Add base metadata to each chunk
        for chunk in chunks:
            chunk["metadata"].update(base_metadata)
            chunk["metadata"]["processor"] = "docling"
            chunk["metadata"]["processing_method"] = "structural_analysis"
        
        return chunks
    
    async def process_multiple_documents(
        self,
        file_paths: List[Path],
        collection_name: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process multiple documents and store in vector database.
        
        Args:
            file_paths: List of file paths to process
            collection_name: Name of Qdrant collection
            metadata: Additional metadata to store
            
        Returns:
            Dictionary with processing results for all documents
        """
        results = []
        total_chunks = 0
        total_points = 0
        
        for file_path in file_paths:
            result = await self.process_document(file_path, collection_name, metadata)
            results.append(result)
            
            if result.get("success"):
                total_chunks += result.get("chunks_created", 0)
                total_points += result.get("points_stored", 0)
        
        successful = sum(1 for r in results if r.get("success"))
        failed = len(results) - successful
        
        return {
            "total_documents": len(file_paths),
            "successful": successful,
            "failed": failed,
            "total_chunks": total_chunks,
            "total_points": total_points,
            "results": results
        }
    
    def get_worker_info(self) -> Dict[str, Any]:
        """Get information about the worker configuration."""
        return {
            "processor_info": self.processor.get_processor_info(),
            "chunker_config": {
                "text_chunk_size": self.chunker.text_chunk_size,
                "text_chunk_overlap": self.chunker.text_chunk_overlap
            }
        }
