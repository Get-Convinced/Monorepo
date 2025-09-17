"""
Docling-based document worker that replaces the basic document worker.
Supports 95+ formats with advanced document understanding.
"""

import logging
import uuid
from typing import Dict, Any, List
from pathlib import Path
from datetime import datetime

try:
    from ..processors.docling_processor import DoclingProcessor
    from ..processors.docling_chunker import DoclingChunker
    from ..embeddings import EmbeddingService
    from ..rag.vector_store import VectorStore
except ImportError:
    # Fallback for when running as script
    from processors.docling_processor import DoclingProcessor
    from processors.docling_chunker import DoclingChunker
    from embeddings import EmbeddingService
    from rag.vector_store import VectorStore

logger = logging.getLogger(__name__)


class DoclingDocumentWorker:
    """
    Advanced document worker using Docling for processing 95+ formats.
    Replaces the basic DocumentWorker with advanced capabilities.
    """
    
    def __init__(self, 
                 embedding_service: EmbeddingService, 
                 vector_store: VectorStore,
                 enable_ocr: bool = True,
                 enable_vlm: bool = True,
                 enable_tables: bool = True,
                 enable_chart_extraction: bool = True):
        """
        Initialize the enhanced Docling document worker with chart extraction.
        
        Args:
            embedding_service: Service for generating embeddings
            vector_store: Vector store for storing embeddings
            enable_ocr: Enable OCR for scanned documents
            enable_vlm: Enable Visual Language Models
            enable_tables: Enable advanced table extraction
            enable_chart_extraction: Enable specialized chart/metrics extraction
        """
        self.embedding_service = embedding_service
        self.vector_store = vector_store
        
        # Initialize enhanced Docling processor with chart extraction
        self.docling_processor = DoclingProcessor(
            enable_ocr=enable_ocr,
            enable_vlm=enable_vlm,
            enable_tables=enable_tables,
            enable_chart_extraction=enable_chart_extraction
        )
        
        # Initialize advanced chunker
        self.docling_chunker = DoclingChunker(
            preserve_structure=True
        )
        
        logger.info(f"Enhanced DoclingDocumentWorker initialized with OCR: {enable_ocr}, VLM: {enable_vlm}, Tables: {enable_tables}, Chart Extraction: {enable_chart_extraction}")
    
    async def process_document(self, 
                              file_path: str, 
                              collection_name: str = "knowledge_base",
                              metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Process a document using Docling's advanced capabilities.
        
        Args:
            file_path: Path to the document file
            collection_name: Name of the vector collection
            metadata: Additional metadata to include
            
        Returns:
            Dictionary containing processing results
        """
        try:
            if metadata is None:
                metadata = {}
            
            file_path_obj = Path(file_path)
            
            # Check if file format is supported
            if not self.docling_processor.is_supported(file_path_obj):
                raise ValueError(f"Unsupported file format: {file_path_obj.suffix}")
            
            logger.info(f"Processing document with Docling: {file_path_obj.name}")
            
            # Process document with Docling
            docling_result = await self.docling_processor.process(file_path_obj)
            
            # Add additional metadata
            docling_result["metadata"].update({
                "processed_at": datetime.utcnow().isoformat(),
                "collection_name": collection_name,
                **metadata
            })
            
            # Create advanced chunks
            chunks = self.docling_chunker.chunk_docling_result(docling_result)
            
            if not chunks:
                raise ValueError("No chunks generated from document")
            
            logger.info(f"Created {len(chunks)} chunks from {file_path_obj.name}")
            
            # Generate embeddings for all chunks
            chunk_contents = [chunk["content"] for chunk in chunks]
            logger.info("Generating embeddings for chunks")
            embeddings = await self.embedding_service.generate_embeddings(chunk_contents)
            
            # Prepare points for vector store with enhanced metadata
            points = []
            for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                point_id = str(uuid.uuid4())
                
                # Enhanced metadata including Docling-specific information
                point_metadata = {
                    "file_path": file_path,
                    "chunk_index": i,
                    "content": chunk["content"],
                    "chunk_type": chunk["chunk_type"],
                    "page_number": chunk["page_number"],
                    "processor": "docling",
                    "processed_at": datetime.utcnow().isoformat(),
                    **docling_result["metadata"],
                    **chunk["metadata"]
                }
                
                points.append({
                    "id": point_id,
                    "vector": embedding,
                    "payload": point_metadata
                })
            
            # Ingest into vector store
            logger.info(f"Ingesting {len(points)} points into collection: {collection_name}")
            await self.vector_store.upsert_points(collection_name, points)
            
            # Get chunk statistics
            chunk_stats = self.docling_chunker.get_chunk_statistics(chunks)
            
            return {
                "success": True,
                "file_path": file_path,
                "chunks_processed": len(chunks),
                "collection_name": collection_name,
                "processor": "docling",
                "chunk_statistics": chunk_stats,
                "structured_elements": docling_result.get("structured_elements", {}),
                "metadata": docling_result["metadata"]
            }
            
        except Exception as e:
            logger.error(f"Error processing document {file_path} with Docling: {e}")
            return {
                "success": False,
                "file_path": file_path,
                "error": str(e),
                "processor": "docling"
            }
    
    async def process_multiple_documents(self, 
                                        file_paths: List[str], 
                                        collection_name: str = "knowledge_base",
                                        metadata: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Process multiple documents using Docling.
        
        Args:
            file_paths: List of file paths to process
            collection_name: Name of the vector collection
            metadata: Additional metadata to include
            
        Returns:
            List of processing results
        """
        results = []
        
        for file_path in file_paths:
            result = await self.process_document(file_path, collection_name, metadata)
            results.append(result)
        
        return results
    
    def get_supported_formats(self) -> List[str]:
        """Get list of all supported file formats."""
        return self.docling_processor.get_supported_formats()
    
    def get_processing_capabilities(self) -> Dict[str, Any]:
        """Get information about processing capabilities."""
        return {
            "processor": "docling",
            "supported_formats": len(self.get_supported_formats()),
            "formats": self.get_supported_formats(),
            "capabilities": {
                "ocr": self.docling_processor.enable_ocr,
                "vlm": self.docling_processor.enable_vlm,
                "tables": self.docling_processor.enable_tables,
                "structured_extraction": True,
                "page_layout_understanding": True,
                "formula_extraction": True,
                "code_extraction": True
            },
            "chunking_strategies": [
                "page_based",
                "content_based", 
                "structured_element"
            ]
        }
    
    async def compare_with_basic_processor(self, file_path: str) -> Dict[str, Any]:
        """
        Compare Docling processing with basic processor (for testing).
        
        Args:
            file_path: Path to the document file
            
        Returns:
            Comparison results
        """
        try:
            # Process with Docling
            docling_result = await self.process_document(file_path, "comparison_test")
            
            # Get basic processing info
            file_path_obj = Path(file_path)
            basic_info = {
                "file_name": file_path_obj.name,
                "file_size": file_path_obj.stat().st_size,
                "file_type": file_path_obj.suffix
            }
            
            return {
                "docling_result": docling_result,
                "basic_info": basic_info,
                "comparison": {
                    "docling_chunks": docling_result.get("chunks_processed", 0),
                    "structured_elements": len(docling_result.get("structured_elements", {})),
                    "processing_enhanced": True
                }
            }
            
        except Exception as e:
            logger.error(f"Error in comparison: {e}")
            return {
                "error": str(e),
                "comparison_failed": True
            }
