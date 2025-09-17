"""
Unified Document Processor
=========================

Handles different file types with appropriate processors:
- PDF/PPT files: GPT models (gpt-4o, gpt-4o-mini, gpt-5)
- Other files: Docling processor

All outputs are embedded via mxbai and stored in vector database.
"""

import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from enum import Enum

from .docling_processor import DoclingProcessor
from .gpt4o_visual_parser import GPT4oVisualParser

logger = logging.getLogger(__name__)


class FileType(Enum):
    """Supported file types for processing."""
    PDF = "pdf"
    PPT = "ppt"
    PPTX = "pptx"
    DOC = "doc"
    DOCX = "docx"
    TXT = "txt"
    MD = "md"
    HTML = "html"
    XML = "xml"


class GPTModel(Enum):
    """Supported GPT models for visual processing."""
    GPT_4O = "gpt-4o"
    GPT_4O_MINI = "gpt-4o-mini"
    GPT_5 = "gpt-5"


class UnifiedDocumentProcessor:
    """
    Unified processor that routes documents to appropriate processors based on file type.
    
    - PDF/PPT files → GPT models for visual analysis
    - Other files → Docling for structural processing
    - All outputs → mxbai embedding → vector storage
    """
    
    def __init__(
        self,
        openai_api_key: str,
        gpt_model: GPTModel = GPTModel.GPT_4O,
        enable_ocr: bool = True,
        enable_vlm: bool = False,
        enable_tables: bool = True,
        enable_chart_extraction: bool = True,
        visual_extraction_dpi: int = 600
    ):
        """
        Initialize unified document processor.
        
        Args:
            openai_api_key: OpenAI API key for GPT models
            gpt_model: GPT model to use for visual processing
            enable_ocr: Enable OCR in Docling
            enable_vlm: Enable VLM in Docling (disabled for GPT files)
            enable_tables: Enable table extraction in Docling
            enable_chart_extraction: Enable chart extraction in Docling
            visual_extraction_dpi: DPI for visual extraction
        """
        self.openai_api_key = openai_api_key
        self.gpt_model = gpt_model
        self.visual_extraction_dpi = visual_extraction_dpi
        
        # Initialize GPT visual parser for PDF/PPT files
        self.gpt_parser = GPT4oVisualParser(
            api_key=openai_api_key,
            model=gpt_model.value
        )
        
        # Initialize Docling processor for other files (disabled for now due to ONNX model issues)
        try:
            self.docling_processor = DoclingProcessor(
                enable_ocr=enable_ocr,
                enable_vlm=enable_vlm,
                enable_tables=enable_tables,
                enable_chart_extraction=enable_chart_extraction
            )
            self.docling_available = True
        except Exception as e:
            logger.warning(f"Docling processor not available: {e}")
            logger.info("Falling back to GPT-only processing for all files")
            self.docling_processor = None
            self.docling_available = False
        
        logger.info(f"Initialized UnifiedDocumentProcessor with GPT model: {gpt_model.value}")
    
    def get_file_type(self, file_path: Path) -> FileType:
        """Determine file type from file extension."""
        extension = file_path.suffix.lower().lstrip('.')
        
        try:
            return FileType(extension)
        except ValueError:
            logger.warning(f"Unsupported file type: {extension}")
            return FileType.TXT  # Default fallback
    
    def is_visual_file(self, file_type: FileType) -> bool:
        """Check if file type should be processed with GPT visual models."""
        return file_type in [FileType.PDF, FileType.PPT, FileType.PPTX]
    
    async def process_document(self, file_path: Path) -> Dict[str, Any]:
        """
        Process document with appropriate processor based on file type.
        
        Args:
            file_path: Path to document file
            
        Returns:
            Dictionary with processing results and metadata
        """
        file_type = self.get_file_type(file_path)
        
        logger.info(f"Processing {file_path.name} (type: {file_type.value})")
        
        if self.is_visual_file(file_type):
            return await self._process_with_gpt(file_path, file_type)
        else:
            if self.docling_available:
                return await self._process_with_docling(file_path, file_type)
            else:
                # Fallback to GPT processing if docling is not available
                logger.info(f"Docling not available, using GPT for {file_type.value} file")
                return await self._process_with_gpt(file_path, file_type)
    
    async def _process_with_gpt(self, file_path: Path, file_type: FileType) -> Dict[str, Any]:
        """Process PDF/PPT files with GPT visual models."""
        logger.info(f"Using GPT {self.gpt_model.value} for visual processing")
        
        try:
            # For PDF files, process all pages
            if file_type == FileType.PDF:
                # Get total pages first
                import fitz
                doc = fitz.open(str(file_path))
                total_pages = len(doc)
                doc.close()
                
                all_content = []
                all_metadata = []
                
                # Process each page
                for page_num in range(total_pages):
                    logger.info(f"Processing page {page_num + 1}/{total_pages}")
                    
                    result = self.gpt_parser.extract_from_pdf_page(
                        pdf_path=str(file_path),
                        page_number=page_num,
                        dpi=self.visual_extraction_dpi
                    )
                    
                    if result.get("content"):
                        all_content.append(result["content"])
                        all_metadata.append({
                            "page_number": page_num + 1,
                            "processor": f"gpt_{self.gpt_model.value}",
                            "file_type": file_type.value,
                            "dpi": self.visual_extraction_dpi,
                            **result
                        })
                
                # Combine all page content
                combined_content = "\n\n--- PAGE BREAK ---\n\n".join(all_content)
                
                return {
                    "content": combined_content,
                    "processor": f"gpt_{self.gpt_model.value}",
                    "file_type": file_type.value,
                    "total_pages": total_pages,
                    "page_metadata": all_metadata,
                    "processing_method": "visual_analysis"
                }
            
            # For PPT files, convert to PDF first (if needed)
            else:
                # TODO: Implement PPT to PDF conversion if needed
                logger.warning(f"PPT processing not yet implemented for {file_path}")
                return {
                    "content": f"PPT file {file_path.name} - processing not implemented",
                    "processor": f"gpt_{self.gpt_model.value}",
                    "file_type": file_type.value,
                    "processing_method": "visual_analysis",
                    "error": "PPT processing not implemented"
                }
                
        except Exception as e:
            logger.error(f"Error processing {file_path} with GPT: {e}")
            return {
                "content": f"Error processing {file_path}: {str(e)}",
                "processor": f"gpt_{self.gpt_model.value}",
                "file_type": file_type.value,
                "processing_method": "visual_analysis",
                "error": str(e)
            }
    
    async def _process_with_docling(self, file_path: Path, file_type: FileType) -> Dict[str, Any]:
        """Process other files with Docling."""
        logger.info(f"Using Docling for {file_type.value} processing")
        
        try:
            result = await self.docling_processor.process(file_path)
            
            return {
                "content": result.get("content", ""),
                "processor": "docling",
                "file_type": file_type.value,
                "processing_method": "structural_analysis",
                "metadata": result.get("metadata", {}),
                "structured_elements": result.get("structured_elements", {})
            }
            
        except Exception as e:
            logger.error(f"Error processing {file_path} with Docling: {e}")
            return {
                "content": f"Error processing {file_path}: {str(e)}",
                "processor": "docling",
                "file_type": file_type.value,
                "processing_method": "structural_analysis",
                "error": str(e)
            }
    
    def get_processor_info(self) -> Dict[str, Any]:
        """Get information about configured processors."""
        info = {
            "gpt_model": self.gpt_model.value,
            "visual_extraction_dpi": self.visual_extraction_dpi,
            "supported_visual_types": [ft.value for ft in [FileType.PDF, FileType.PPT, FileType.PPTX]],
            "docling_available": self.docling_available
        }
        
        if self.docling_available:
            info["supported_docling_types"] = [ft.value for ft in FileType if ft not in [FileType.PDF, FileType.PPT, FileType.PPTX]]
            info["docling_config"] = {
                "enable_ocr": self.docling_processor.enable_ocr,
                "enable_vlm": self.docling_processor.enable_vlm,
                "enable_tables": self.docling_processor.enable_tables,
                "enable_chart_extraction": self.docling_processor.enable_chart_extraction
            }
        else:
            info["supported_docling_types"] = []
            info["docling_config"] = None
            info["fallback_mode"] = "All files will be processed with GPT models"
        
        return info
