"""
Advanced chunking strategy for Docling-processed documents.
Handles structured elements like tables, figures, and formulas separately.
"""

import logging
from typing import List, Dict, Any, Optional
from langchain_text_splitters import RecursiveCharacterTextSplitter
from datetime import datetime

logger = logging.getLogger(__name__)


class DoclingChunker:
    """
    Advanced chunking strategy that preserves document structure
    and creates specialized chunks for different content types.
    """
    
    def __init__(self, 
                 text_chunk_size: int = 1000,
                 text_chunk_overlap: int = 200,
                 table_chunk_size: int = 2000,
                 preserve_structure: bool = True):
        """
        Initialize the Docling chunker.
        
        Args:
            text_chunk_size: Size for regular text chunks
            text_chunk_overlap: Overlap between text chunks
            table_chunk_size: Size for table chunks (usually larger)
            preserve_structure: Whether to preserve document structure
        """
        self.text_chunk_size = text_chunk_size
        self.text_chunk_overlap = text_chunk_overlap
        self.table_chunk_size = table_chunk_size
        self.preserve_structure = preserve_structure
        
        # Initialize text splitter for regular content
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=text_chunk_size,
            chunk_overlap=text_chunk_overlap,
            length_function=len,
        )
        
        # Initialize table splitter (larger chunks for tables)
        self.table_splitter = RecursiveCharacterTextSplitter(
            chunk_size=table_chunk_size,
            chunk_overlap=100,  # Less overlap for tables
            length_function=len,
        )
        
        logger.info(f"DoclingChunker initialized with text_chunk_size={text_chunk_size}, preserve_structure={preserve_structure}")
    
    def chunk_docling_result(self, docling_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Chunk a Docling processing result into structured chunks.
        
        Args:
            docling_result: Result from DoclingProcessor.process()
            
        Returns:
            List of structured chunks
        """
        chunks = []
        
        # Extract basic info
        content = docling_result.get("content", "")
        metadata = docling_result.get("metadata", {})
        structured_elements = docling_result.get("structured_elements", {})
        
        # Create page-based chunks if structure should be preserved
        if self.preserve_structure and "page_statistics" in metadata:
            chunks.extend(self._create_page_based_chunks(content, metadata, structured_elements))
        else:
            # Create content-based chunks
            chunks.extend(self._create_content_based_chunks(content, metadata, structured_elements))
        
        # Add structured element chunks
        chunks.extend(self._create_structured_element_chunks(structured_elements, metadata))
        
        logger.info(f"Created {len(chunks)} chunks from Docling result")
        return chunks
    
    def _create_page_based_chunks(self, content: str, metadata: Dict[str, Any], structured_elements: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create chunks based on page structure using content offsets for accurate page numbers."""
        chunks: List[Dict[str, Any]] = []
        page_stats = metadata.get("page_statistics", [])
        
        # Precompute cumulative page boundaries in the concatenated markdown
        # boundaries[i] = end offset (exclusive) of page i in concatenated string
        boundaries: List[int] = []
        running_total = 0
        for stat in page_stats:
            running_total += stat.get("text_length", 0)
            boundaries.append(running_total)
        
        # Split, then map each chunk to its start offset and from there to a page
        text_chunks = self.text_splitter.split_text(content)
        search_pos = 0  # moving cursor to avoid matching earlier identical substrings
        
        def locate_page(start_index: int) -> int:
            if not boundaries:
                return 0
            for idx, end_offset in enumerate(boundaries):
                if start_index < end_offset:
                    # page numbers in metadata likely 1-based or from 'page_number'
                    # Prefer exact page_number if present, else (idx+1)
                    return page_stats[idx].get("page_number", idx + 1)
            # Fallback to last page
            last = page_stats[-1].get("page_number", len(boundaries))
            return last
        
        for i, chunk_text in enumerate(text_chunks):
            start_idx = content.find(chunk_text, search_pos)
            if start_idx == -1:
                # If not found (highly unlikely), do not move search_pos; assign unknown page
                page_number = 0
            else:
                page_number = locate_page(start_idx)
                # Advance cursor near the end of this chunk to continue forward search
                search_pos = start_idx + max(1, len(chunk_text) // 2)
            
            chunk = {
                "content": chunk_text,
                "chunk_type": "text",
                "chunk_index": i,
                "page_number": page_number,
                "metadata": {
                    "source": metadata.get("file_name", "unknown"),
                    "processor": "docling",
                    "chunking_strategy": "page_based",
                    "created_at": datetime.utcnow().isoformat()
                }
            }
            chunks.append(chunk)
        
        return chunks
    
    def _create_content_based_chunks(self, content: str, metadata: Dict[str, Any], structured_elements: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create chunks based on content without page structure."""
        chunks = []
        text_chunks = self.text_splitter.split_text(content)
        
        for i, chunk_text in enumerate(text_chunks):
            chunk = {
                "content": chunk_text,
                "chunk_type": "text",
                "chunk_index": i,
                "page_number": 0,  # Unknown page
                "metadata": {
                    "source": metadata.get("file_name", "unknown"),
                    "processor": "docling",
                    "chunking_strategy": "content_based",
                    "created_at": datetime.utcnow().isoformat()
                }
            }
            chunks.append(chunk)
        
        return chunks
    
    def _create_structured_element_chunks(self, structured_elements: Dict[str, Any], metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create specialized chunks for structured elements."""
        chunks = []
        
        # Table chunks
        for table in structured_elements.get("tables", []):
            table_chunk = {
                "content": table.get("markdown", ""),
                "chunk_type": "table",
                "chunk_index": len(chunks),
                "page_number": table.get("page", 0),
                "metadata": {
                    "source": metadata.get("file_name", "unknown"),
                    "processor": "docling",
                    "chunking_strategy": "structured_element",
                    "element_type": "table",
                    "table_index": table.get("index", 0),
                    "table_structure": table.get("structure", {}),
                    "created_at": datetime.utcnow().isoformat()
                }
            }
            chunks.append(table_chunk)
        
        # Figure chunks
        for figure in structured_elements.get("figures", []):
            figure_content = f"Figure: {figure.get('caption', '')}\nDescription: {figure.get('description', '')}"
            figure_chunk = {
                "content": figure_content,
                "chunk_type": "figure",
                "chunk_index": len(chunks),
                "page_number": figure.get("page", 0),
                "metadata": {
                    "source": metadata.get("file_name", "unknown"),
                    "processor": "docling",
                    "chunking_strategy": "structured_element",
                    "element_type": "figure",
                    "figure_index": figure.get("index", 0),
                    "figure_type": figure.get("type", "unknown"),
                    "created_at": datetime.utcnow().isoformat()
                }
            }
            chunks.append(figure_chunk)
        
        # Formula chunks
        for formula in structured_elements.get("formulas", []):
            formula_content = f"Formula: {formula.get('latex', '')}\nText: {formula.get('text', '')}"
            formula_chunk = {
                "content": formula_content,
                "chunk_type": "formula",
                "chunk_index": len(chunks),
                "page_number": formula.get("page", 0),
                "metadata": {
                    "source": metadata.get("file_name", "unknown"),
                    "processor": "docling",
                    "chunking_strategy": "structured_element",
                    "element_type": "formula",
                    "formula_index": formula.get("index", 0),
                    "created_at": datetime.utcnow().isoformat()
                }
            }
            chunks.append(formula_chunk)
        
        # Code block chunks
        for code_block in structured_elements.get("code_blocks", []):
            code_content = f"Code ({code_block.get('language', 'unknown')}):\n{code_block.get('code', '')}"
            code_chunk = {
                "content": code_content,
                "chunk_type": "code",
                "chunk_index": len(chunks),
                "page_number": code_block.get("page", 0),
                "metadata": {
                    "source": metadata.get("file_name", "unknown"),
                    "processor": "docling",
                    "chunking_strategy": "structured_element",
                    "element_type": "code",
                    "code_index": code_block.get("index", 0),
                    "language": code_block.get("language", "unknown"),
                    "created_at": datetime.utcnow().isoformat()
                }
            }
            chunks.append(code_chunk)
        
        return chunks
    
    def _estimate_page_number(self, chunk_text: str, page_stats: List[Dict[str, Any]]) -> int:
        """Estimate which page a chunk belongs to based on content length."""
        if not page_stats:
            return 0
        
        # Simple heuristic: estimate based on text length
        # This could be improved with more sophisticated page detection
        cumulative_length = 0
        for page_stat in page_stats:
            cumulative_length += page_stat.get("text_length", 0)
            if len(chunk_text) <= cumulative_length:
                return page_stat.get("page_number", 0)
        
        # If we can't determine, return the last page
        return page_stats[-1].get("page_number", 0) if page_stats else 0
    
    def get_chunk_statistics(self, chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Get statistics about the created chunks."""
        stats = {
            "total_chunks": len(chunks),
            "chunk_types": {},
            "pages_covered": set(),
            "avg_chunk_size": 0
        }
        
        total_size = 0
        for chunk in chunks:
            chunk_type = chunk.get("chunk_type", "unknown")
            stats["chunk_types"][chunk_type] = stats["chunk_types"].get(chunk_type, 0) + 1
            
            page_num = chunk.get("page_number", 0)
            if page_num > 0:
                stats["pages_covered"].add(page_num)
            
            total_size += len(chunk.get("content", ""))
        
        stats["pages_covered"] = len(stats["pages_covered"])
        stats["avg_chunk_size"] = total_size // len(chunks) if chunks else 0
        
        return stats
