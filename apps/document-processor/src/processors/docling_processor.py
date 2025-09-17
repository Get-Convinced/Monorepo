"""
Enhanced Docling-based document processor with VLM and chart extraction.
This version includes advanced visual understanding for PPT-to-PDF files.
"""

import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
import json

from docling.document_converter import DocumentConverter
from docling.datamodel.base_models import DocInputType
from docling.document_converter import PipelineOptions
from .base_processor import BaseDocumentProcessor

logger = logging.getLogger(__name__)


class DoclingProcessor(BaseDocumentProcessor):
    """
    Enhanced document processor using Docling with VLM and chart extraction.
    Supports 95+ formats with advanced PDF understanding, OCR, and VLM capabilities.
    Specifically designed to capture numbers from PPT-to-PDF exports.
    """
    
    def __init__(self, enable_ocr: bool = True, enable_vlm: bool = True, enable_tables: bool = True, enable_chart_extraction: bool = True):
        super().__init__()
        """
        Initialize enhanced Docling processor with VLM and chart extraction.
        
        Args:
            enable_ocr: Enable OCR for scanned documents
            enable_vlm: Enable Visual Language Models for image understanding
            enable_tables: Enable advanced table structure extraction
            enable_chart_extraction: Enable specialized chart/metrics extraction
        """
        self.enable_ocr = enable_ocr
        self.enable_vlm = enable_vlm
        self.enable_tables = enable_tables
        self.enable_chart_extraction = enable_chart_extraction
        
        # Configure enhanced pipeline options for VLM and chart extraction
        self.pipeline_options = PipelineOptions()
        
        # Enable basic features
        self.pipeline_options.do_ocr = self.enable_ocr
        self.pipeline_options.do_table_structure = self.enable_tables
        
        # Enable VLM features for chart understanding
        if self.enable_vlm:
            # Enable picture description and classification
            self.pipeline_options.do_picture_description = True
            self.pipeline_options.do_picture_classification = True
            
            # Enable chart-specific processing (when available)
            if self.enable_chart_extraction:
                # Note: Chart understanding is coming soon in Docling
                # For now, we'll use enhanced OCR and picture processing
                self.pipeline_options.do_ocr = True  # Ensure OCR is enabled for graphics
                self.pipeline_options.do_picture_description = True
                self.pipeline_options.do_picture_classification = True
        
        # Initialize converter with enhanced options
        try:
            self.converter = DocumentConverter()
        except Exception as e:
            logger.warning(f"Failed to initialize DocumentConverter with default settings: {e}")
            logger.info("Attempting to initialize with minimal configuration...")
            # Try to initialize with minimal configuration
            try:
                from docling.document_converter import DocumentConverter
                from docling.pipeline.base_model_pipeline import BaseModelPipeline
                
                # Create a minimal pipeline that doesn't require ONNX models
                class MinimalPipeline(BaseModelPipeline):
                    def __init__(self):
                        super().__init__()
                        # Disable layout model that requires ONNX
                        self.layout_model = None
                        self.table_model = None
                
                # Initialize converter with minimal pipeline
                self.converter = DocumentConverter(pipeline=MinimalPipeline())
                logger.info("Successfully initialized DocumentConverter with minimal configuration")
            except Exception as e2:
                logger.error(f"Failed to initialize DocumentConverter even with minimal configuration: {e2}")
                raise
        
        # Modify the existing PDF format options to enable VLM features
        from docling.datamodel.base_models import DocInputType
        if DocInputType.PDF in self.converter.format_to_options:
            pdf_options = self.converter.format_to_options[DocInputType.PDF]
            if hasattr(pdf_options.pipeline_options, 'do_picture_description'):
                pdf_options.pipeline_options.do_picture_description = self.enable_vlm
            if hasattr(pdf_options.pipeline_options, 'do_picture_classification'):
                pdf_options.pipeline_options.do_picture_classification = self.enable_vlm
            if hasattr(pdf_options.pipeline_options, 'do_ocr'):
                pdf_options.pipeline_options.do_ocr = self.enable_ocr
            if hasattr(pdf_options.pipeline_options, 'do_table_structure'):
                pdf_options.pipeline_options.do_table_structure = self.enable_tables
            
            # Enhanced VLM configuration for better visual element capture
            if self.enable_vlm and hasattr(pdf_options.pipeline_options, 'picture_description_options'):
                vlm_opts = pdf_options.pipeline_options.picture_description_options
                # Lower the area threshold to capture smaller visual elements
                vlm_opts.picture_area_threshold = 0.01  # Much lower threshold
                vlm_opts.scale = 3  # Higher scale for better OCR
                # Enhanced prompt for better number extraction
                vlm_opts.prompt = "Describe this image in detail, focusing on any numbers, percentages, ratios, or text visible in the image. Include all numerical values you can see."
                vlm_opts.generation_config['max_new_tokens'] = 300  # More tokens for detailed descriptions
            
            # Enable picture image generation for better processing
            if hasattr(pdf_options.pipeline_options, 'generate_picture_images'):
                pdf_options.pipeline_options.generate_picture_images = self.enable_vlm
        
        logger.info(f"Enhanced DoclingProcessor initialized with OCR: {enable_ocr}, VLM: {enable_vlm}, Tables: {enable_tables}, Chart Extraction: {enable_chart_extraction}")
    
    def extract_text(self, file_path: str) -> str:
        """Extract text content from document (synchronous version)."""
        try:
            result = self.converter.convert(file_path, pipeline_options=self.pipeline_options)
            return result.document.export_to_markdown()
        except Exception as e:
            logger.error(f"Error extracting text from {file_path}: {e}")
            raise
    
    def extract_metadata(self, file_path: str) -> Dict[str, Any]:
        """Extract metadata from document (synchronous version)."""
        try:
            result = self.converter.convert(file_path, pipeline_options=self.pipeline_options)
            file_path_obj = Path(file_path)
            
            metadata = {
                "file_name": file_path_obj.name,
                "file_type": file_path_obj.suffix.lower(),
                "size_bytes": file_path_obj.stat().st_size,
                "processor": "docling",
                "pages": len(result.document.pages) if hasattr(result.document, 'pages') else 0
            }
            
            return metadata
        except Exception as e:
            logger.error(f"Error extracting metadata from {file_path}: {e}")
            raise
    
    async def process(self, file_path: Path) -> Dict[str, Any]:
        """
        Process a document using Docling's advanced capabilities.
        
        Args:
            file_path: Path to the document file
            
        Returns:
            Dictionary containing processed content and metadata
        """
        if not file_path.is_file():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        try:
            logger.info(f"Processing document with Docling: {file_path.name}")
            
            # Convert document using Docling (pipeline options configured in converter)
            result = self.converter.convert(str(file_path))
            
            # Extract basic content
            content = result.document.export_to_markdown()
            
            # Extract comprehensive metadata
            metadata = await self._extract_metadata(result, file_path)
            
            # Extract structured elements
            structured_elements = await self._extract_structured_elements(result)
            
            logger.info(f"Successfully processed {file_path.name} with Docling")
            
            return {
                "content": content,
                "metadata": metadata,
                "structured_elements": structured_elements,
                "processor": "docling",
                "processing_time": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error processing document {file_path} with Docling: {e}")
            raise
    
    async def _extract_metadata(self, result, file_path: Path) -> Dict[str, Any]:
        """Extract comprehensive metadata from Docling result."""
        metadata = {
            "file_name": file_path.name,
            "file_type": file_path.suffix.lower(),
            "size_bytes": file_path.stat().st_size,
            "processor": "docling",
            "docling_version": "2.52.0",
            "pages": len(result.document.pages) if hasattr(result.document, 'pages') else 0,
            "processing_options": {
                "ocr_enabled": self.enable_ocr,
                "vlm_enabled": self.enable_vlm,
                "tables_enabled": self.enable_tables
            }
        }
        
        # Extract document-level metadata if available
        if hasattr(result.document, 'name'):
            metadata["document_name"] = result.document.name
        
        if hasattr(result.document, 'title'):
            metadata["title"] = result.document.title
        
        if hasattr(result.document, 'authors'):
            metadata["authors"] = result.document.authors
        
        # Extract page-level statistics
        if hasattr(result.document, 'pages'):
            page_stats = []
            for page_key, page in result.document.pages.items():
                page_info = {
                    "page_number": page.page_no,  # Use the actual page_no attribute
                    "text_length": len(page.export_to_markdown()) if hasattr(page, 'export_to_markdown') else 0
                }
                
                # Count elements on page
                if hasattr(page, 'tables'):
                    page_info["tables_count"] = len(page.tables)
                if hasattr(page, 'figures'):
                    page_info["figures_count"] = len(page.figures)
                
                page_stats.append(page_info)
            
            metadata["page_statistics"] = page_stats
        
        return metadata
    
    async def _extract_structured_elements(self, result) -> Dict[str, Any]:
        """Extract structured elements like tables, figures, formulas, and chart metrics."""
        structured_elements = {
            "tables": [],
            "figures": [],
            "formulas": [],
            "code_blocks": [],
            "chart_metrics": [],  # New: extracted metrics from charts
            "visual_elements": []  # New: other visual elements with text
        }
        
        if not hasattr(result.document, 'pages'):
            return structured_elements
        
        for page_key, page in result.document.pages.items():
            page_no = page.page_no
            
            # Extract tables
            if hasattr(page, 'tables') and self.enable_tables:
                for i, table in enumerate(page.tables):
                    table_data = {
                        "page": page_no,
                        "index": i,
                        "markdown": table.export_to_markdown(),
                        "structure": self._extract_table_structure(table),
                        "cells": self._extract_cell_data(table)
                    }
                    structured_elements["tables"].append(table_data)
            
            # Extract figures with enhanced VLM processing
            if hasattr(page, 'figures') and self.enable_vlm:
                for i, figure in enumerate(page.figures):
                    figure_data = {
                        "page": page_no,
                        "index": i,
                        "caption": getattr(figure, 'caption', ''),
                        "description": getattr(figure, 'description', ''),
                        "type": getattr(figure, 'type', 'unknown'),
                        "bbox": getattr(figure, 'bbox', None)
                    }
                    
                    # Enhanced chart processing for PPT-to-PDF files
                    if self.enable_chart_extraction:
                        chart_metrics = await self._extract_chart_metrics(figure, page_no, i)
                        if chart_metrics:
                            structured_elements["chart_metrics"].extend(chart_metrics)
                    
                    structured_elements["figures"].append(figure_data)
            
            # Extract visual elements with text (for PPT-to-PDF graphics)
            if self.enable_chart_extraction:
                visual_elements = await self._extract_visual_elements(page, page_no)
                if visual_elements:
                    structured_elements["visual_elements"].extend(visual_elements)
            
            # Extract formulas (if available)
            if hasattr(page, 'formulas'):
                for i, formula in enumerate(page.formulas):
                    formula_data = {
                        "page": page_no,
                        "index": i,
                        "latex": getattr(formula, 'latex', ''),
                        "text": getattr(formula, 'text', ''),
                        "bbox": getattr(formula, 'bbox', None)
                    }
                    structured_elements["formulas"].append(formula_data)
            
            # Extract code blocks (if available)
            if hasattr(page, 'code_blocks'):
                for i, code_block in enumerate(page.code_blocks):
                    code_data = {
                        "page": page_no,
                        "index": i,
                        "code": getattr(code_block, 'code', ''),
                        "language": getattr(code_block, 'language', 'unknown'),
                        "bbox": getattr(code_block, 'bbox', None)
                    }
                    structured_elements["code_blocks"].append(code_data)
        
        return structured_elements
    
    def _extract_table_structure(self, table) -> Dict[str, Any]:
        """Extract table structure information."""
        structure = {
            "rows": 0,
            "columns": 0,
            "has_header": False,
            "cell_count": 0
        }
        
        if hasattr(table, 'rows'):
            structure["rows"] = len(table.rows)
        if hasattr(table, 'columns'):
            structure["columns"] = len(table.columns)
        if hasattr(table, 'has_header'):
            structure["has_header"] = table.has_header
        if hasattr(table, 'cells'):
            structure["cell_count"] = len(table.cells)
        
        return structure
    
    def _extract_cell_data(self, table) -> List[Dict[str, Any]]:
        """Extract individual cell data from table."""
        cells = []
        
        if hasattr(table, 'cells'):
            for cell in table.cells:
                cell_data = {
                    "text": getattr(cell, 'text', ''),
                    "row": getattr(cell, 'row', 0),
                    "column": getattr(cell, 'column', 0),
                    "type": getattr(cell, 'type', 'unknown'),
                    "bbox": getattr(cell, 'bbox', None)
                }
                cells.append(cell_data)
        
        return cells
    
    def get_supported_formats(self) -> List[str]:
        """Get list of supported file formats."""
        return [
            # Document formats
            '.pdf', '.docx', '.doc', '.pptx', '.ppt', '.xlsx', '.xls',
            # Text formats
            '.txt', '.md', '.rtf', '.odt', '.ods', '.odp',
            # Web formats
            '.html', '.htm', '.xml', '.json', '.csv',
            # Image formats
            '.png', '.jpg', '.jpeg', '.tiff', '.bmp', '.gif', '.webp',
            # Audio formats
            '.wav', '.mp3', '.m4a', '.flac', '.ogg',
            # Archive formats
            '.zip', '.tar', '.gz',
            # And many more...
        ]
    
    def is_supported(self, file_path: Path) -> bool:
        """Check if file format is supported."""
        return file_path.suffix.lower() in self.get_supported_formats()
    
    async def _extract_chart_metrics(self, figure, page_no: int, figure_index: int) -> List[Dict[str, Any]]:
        """
        Extract metrics and numerical data from chart figures.
        This is designed to capture numbers from PPT-to-PDF exports.
        """
        chart_metrics = []
        
        try:
            # Get figure description and caption for VLM-extracted content
            description = getattr(figure, 'description', '')
            caption = getattr(figure, 'caption', '')
            
            # Also try to get picture description if available
            picture_description = getattr(figure, 'picture_description', '')
            
            # Combine all available text for analysis
            combined_text = f"{caption} {description} {picture_description}".strip()
            
            if combined_text:
                # Extract numerical patterns (percentages, ratios, multipliers)
                import re
                
                # Pattern for percentages: 81%, -3.3%
                percentage_pattern = r'(-?\d+\.?\d*%)'
                percentages = re.findall(percentage_pattern, combined_text)
                
                # Pattern for ratios/multipliers: 7.5x, 8x, 4x
                ratio_pattern = r'(\d+\.?\d*x)'
                ratios = re.findall(ratio_pattern, combined_text)
                
                # Pattern for time periods: 26 months, 2 years
                time_pattern = r'(\d+\s*(?:months?|years?|days?|weeks?))'
                time_periods = re.findall(time_pattern, combined_text, re.IGNORECASE)
                
                # Pattern for general numbers with context
                number_pattern = r'(\d+\.?\d*)'
                numbers = re.findall(number_pattern, combined_text)
                
                # Create metric entries
                for percentage in percentages:
                    chart_metrics.append({
                        "page": page_no,
                        "figure_index": figure_index,
                        "metric_type": "percentage",
                        "value": percentage,
                        "context": combined_text,
                        "bbox": getattr(figure, 'bbox', None),
                        "extraction_method": "vlm_description"
                    })
                
                for ratio in ratios:
                    chart_metrics.append({
                        "page": page_no,
                        "figure_index": figure_index,
                        "metric_type": "ratio",
                        "value": ratio,
                        "context": combined_text,
                        "bbox": getattr(figure, 'bbox', None),
                        "extraction_method": "vlm_description"
                    })
                
                for time_period in time_periods:
                    chart_metrics.append({
                        "page": page_no,
                        "figure_index": figure_index,
                        "metric_type": "time_period",
                        "value": time_period,
                        "context": combined_text,
                        "bbox": getattr(figure, 'bbox', None),
                        "extraction_method": "vlm_description"
                    })
                
                # For significant numbers (likely metrics)
                for number in numbers:
                    if float(number) > 1:  # Filter out small numbers that might be noise
                        chart_metrics.append({
                            "page": page_no,
                            "figure_index": figure_index,
                            "metric_type": "number",
                            "value": number,
                            "context": combined_text,
                            "bbox": getattr(figure, 'bbox', None),
                            "extraction_method": "vlm_description"
                        })
            
            logger.info(f"Extracted {len(chart_metrics)} chart metrics from figure {figure_index} on page {page_no}")
            
        except Exception as e:
            logger.warning(f"Error extracting chart metrics from figure {figure_index} on page {page_no}: {e}")
        
        return chart_metrics
    
    async def _extract_visual_elements(self, page, page_no: int) -> List[Dict[str, Any]]:
        """
        Extract visual elements with text content from pages.
        This helps capture text that might be in graphics or visual elements.
        """
        visual_elements = []
        
        try:
            # Get page content for analysis
            page_content = page.export_to_markdown() if hasattr(page, 'export_to_markdown') else ""
            
            if page_content:
                # Look for patterns that might indicate visual elements with metrics
                import re
                
                # Pattern for metric-like text (label: value)
                metric_pattern = r'([A-Za-z\s]+):\s*([+-]?\d+\.?\d*[%x]?)'
                metrics = re.findall(metric_pattern, page_content)
                
                for label, value in metrics:
                    visual_elements.append({
                        "page": page_no,
                        "element_type": "metric",
                        "label": label.strip(),
                        "value": value.strip(),
                        "context": page_content,
                        "extraction_method": "text_analysis"
                    })
                
                # Pattern for standalone percentages and ratios
                standalone_pattern = r'\b(\d+\.?\d*[%x])\b'
                standalone_values = re.findall(standalone_pattern, page_content)
                
                for value in standalone_values:
                    visual_elements.append({
                        "page": page_no,
                        "element_type": "standalone_value",
                        "value": value,
                        "context": page_content,
                        "extraction_method": "text_analysis"
                    })
            
            logger.info(f"Extracted {len(visual_elements)} visual elements from page {page_no}")
            
        except Exception as e:
            logger.warning(f"Error extracting visual elements from page {page_no}: {e}")
        
        return visual_elements
