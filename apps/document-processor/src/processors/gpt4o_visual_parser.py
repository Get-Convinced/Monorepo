"""
GPT-4o-mini Visual Parser for extracting content from document images.
Designed to work alongside Docling for comprehensive document processing.
"""

import logging
import base64
import io
from pathlib import Path
from typing import Dict, Any, List, Optional
import json
from PIL import Image
import fitz  # PyMuPDF for PDF to image conversion

try:
    import openai
except ImportError:
    openai = None

logger = logging.getLogger(__name__)


class GPT4oVisualParser:
    """
    Visual parser using GPT-5 for extracting content from document images.
    Focuses on charts, figures, logos, and visual elements that traditional OCR misses.
    Uses the cutting-edge GPT-5 model for maximum visual analysis capabilities.
    """
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-5"):
        """
        Initialize GPT-5 visual parser.
        
        Args:
            api_key: OpenAI API key (if None, will use environment variable)
            model: OpenAI model to use (gpt-5 for cutting-edge visual analysis)
        """
        if openai is None:
            raise ImportError("OpenAI library not installed. Run: pip install openai")
        
        self.client = openai.OpenAI(api_key=api_key)
        self.model = model
        
        # General-purpose prompt for comprehensive document content extraction
        self.extraction_prompt = """
You are a document analysis expert. Please analyze this slide/image and extract all the content you can see.

Please provide:

## 📄 TEXT CONTENT
Extract all readable text including:
- Headings and titles
- Body text and descriptions
- Labels and captions
- Numbers, percentages, and metrics
- Any other text content

## 📊 DATA AND METRICS
List any numbers, statistics, or data points you can identify:
- Percentages and ratios
- Financial figures
- Time periods
- Quantities and measurements
- Any numerical data

## 📈 VISUAL ELEMENTS
Describe any visual elements:
- Charts, graphs, or diagrams
- Images or logos
- Callouts or highlights
- Tables or lists

## 🎯 KEY INFORMATION
Summarize the main points and purpose of this slide.

Be thorough but focus on what you can actually see and read clearly.
"""
    
    def extract_from_pdf_page(self, pdf_path: str, page_number: int, dpi: int = 300) -> Dict[str, Any]:
        """
        Extract visual content from a specific PDF page using GPT-4o-mini.
        
        Args:
            pdf_path: Path to PDF file
            page_number: Page number (0-based)
            dpi: DPI for image conversion (higher = better quality)
            
        Returns:
            Dictionary with extracted content and metadata
        """
        try:
            # Convert PDF page to image
            image_data = self._pdf_page_to_image(pdf_path, page_number, dpi)
            
            # Extract content using GPT-4o-mini
            extraction_result = self._extract_from_image(image_data)
            
            # Add metadata
            result = {
                "page_number": page_number + 1,  # Convert to 1-based
                "pdf_path": pdf_path,
                "extraction_method": "gpt4o_visual",
                "model": self.model,
                "dpi": dpi,
                **extraction_result
            }
            
            logger.info(f"Successfully extracted visual content from page {page_number + 1}")
            return result
            
        except Exception as e:
            logger.error(f"Error extracting from PDF page {page_number}: {e}")
            return {
                "page_number": page_number + 1,
                "error": str(e),
                "extraction_method": "gpt4o_visual",
                "content": "",
                "numbers_found": [],
                "logos_found": []
            }
    
    def _pdf_page_to_image(self, pdf_path: str, page_number: int, dpi: int = 300) -> bytes:
        """Convert PDF page to high-quality image."""
        try:
            # Open PDF
            pdf_document = fitz.open(pdf_path)
            
            if page_number >= len(pdf_document):
                raise ValueError(f"Page {page_number} not found in PDF (total pages: {len(pdf_document)})")
            
            # Get page
            page = pdf_document[page_number]
            
            # Create transformation matrix for high DPI
            mat = fitz.Matrix(dpi / 72, dpi / 72)  # 72 is default DPI
            
            # Render page to image
            pix = page.get_pixmap(matrix=mat)
            
            # Convert to PIL Image
            img_data = pix.tobytes("png")
            
            pdf_document.close()
            return img_data
            
        except Exception as e:
            logger.error(f"Error converting PDF page to image: {e}")
            raise
    
    def _extract_from_image(self, image_data: bytes) -> Dict[str, Any]:
        """Extract content from image using GPT-4o-mini."""
        try:
            # Encode image to base64
            base64_image = base64.b64encode(image_data).decode('utf-8')
            
            # Create message for GPT-4o-mini
            messages = [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": self.extraction_prompt
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{base64_image}",
                                "detail": "high"  # High detail for better number extraction
                            }
                        }
                    ]
                }
            ]
            
            # Call GPT-4o/GPT-5
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                # max_tokens=2000,  # Use max_tokens for compatibility
                # temperature=0.1   # Low temperature for consistent extraction
            )
            
            # Extract response content
            extracted_content = response.choices[0].message.content
            
            # Print the full GPT-5 output for debugging
            print("=" * 80)
            print("🚀 FULL GPT-5 OUTPUT:")
            print("=" * 80)
            print(extracted_content)
            print("=" * 80)
            
            # Parse the structured response
            parsed_result = self._parse_extraction_response(extracted_content)
            
            return {
                "content": extracted_content,
                "parsed_content": parsed_result,
                "token_usage": response.usage.total_tokens if response.usage else 0,
                "model": self.model
            }
            
        except Exception as e:
            logger.error(f"Error extracting from image with GPT-4o-mini: {e}")
            return {
                "content": f"Error: {str(e)}",
                "parsed_content": {},
                "numbers_found": [],
                "logos_found": [],
                "error": str(e)
            }
    
    def _parse_extraction_response(self, content: str) -> Dict[str, Any]:
        """Parse the structured response from GPT-4o-mini."""
        try:
            # Extract numbers using regex patterns
            import re
            
            # Pattern for percentages: 81%, -3.3%
            percentages = re.findall(r'(-?\d+\.?\d*%)', content)
            
            # Pattern for ratios/multipliers: 7.5x, 8x
            ratios = re.findall(r'(\d+\.?\d*x)', content, re.IGNORECASE)
            
            # Pattern for time periods: 26 months, 2 years
            time_periods = re.findall(r'(\d+\s*(?:months?|years?|days?|weeks?))', content, re.IGNORECASE)
            
            # Pattern for currency: $1.5mn, USD 9.1m
            currency = re.findall(r'((?:\$|USD)\s*\d+\.?\d*[kmb]?n?)', content, re.IGNORECASE)
            
            # Pattern for general numbers
            numbers = re.findall(r'(\d+\.?\d+)', content)
            
            # Extract logos/brands (look for common patterns)
            logo_patterns = [
                r'logo[s]?[:\s]+([A-Z][A-Za-z\s&]+)',
                r'brand[s]?[:\s]+([A-Z][A-Za-z\s&]+)',
                r'company[:\s]+([A-Z][A-Za-z\s&]+)'
            ]
            
            logos_found = []
            for pattern in logo_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                logos_found.extend(matches)
            
            # Look for specific business terms
            business_metrics = []
            metric_patterns = [
                r'(gross margin[:\s]*\d+\.?\d*%?)',
                r'(revenue churn[:\s]*-?\d+\.?\d*%?)',
                r'(net dollar retention[:\s]*\d+\.?\d*%?)',
                r'(LTV[:\s]*CAC[:\s]*\d+\.?\d*x?)',
                r'(breakeven[:\s]*\d+\.?\d*\s*months?)',
                r'(enterprise[:\s]*account[:\s]*\d+\.?\d*x?)',
                r'(mid-?market[:\s]*account[:\s]*\d+\.?\d*x?)'
            ]
            
            for pattern in metric_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                business_metrics.extend(matches)
            
            return {
                "numbers_found": {
                    "percentages": list(set(percentages)),
                    "ratios": list(set(ratios)),
                    "time_periods": list(set(time_periods)),
                    "currency": list(set(currency)),
                    "all_numbers": list(set(numbers))
                },
                "logos_found": list(set(logos_found)),
                "business_metrics": list(set(business_metrics)),
                "content_length": len(content)
            }
            
        except Exception as e:
            logger.warning(f"Error parsing extraction response: {e}")
            return {
                "numbers_found": {},
                "logos_found": [],
                "business_metrics": [],
                "parse_error": str(e)
            }
    
    def extract_from_multiple_pages(self, pdf_path: str, page_numbers: List[int], dpi: int = 300) -> List[Dict[str, Any]]:
        """
        Extract visual content from multiple PDF pages.
        
        Args:
            pdf_path: Path to PDF file
            page_numbers: List of page numbers (0-based)
            dpi: DPI for image conversion
            
        Returns:
            List of extraction results for each page
        """
        results = []
        
        for page_num in page_numbers:
            logger.info(f"Processing page {page_num + 1} with GPT-4o-mini...")
            result = self.extract_from_pdf_page(pdf_path, page_num, dpi)
            results.append(result)
        
        return results
    
    def should_use_visual_extraction(self, docling_page_info: Dict[str, Any]) -> bool:
        """
        Determine if a page should use GPT-4o-mini visual extraction.
        
        Args:
            docling_page_info: Page information from Docling processing
            
        Returns:
            True if page should use visual extraction
        """
        # Criteria for using visual extraction
        figures_count = docling_page_info.get("figures_count", 0)
        tables_count = docling_page_info.get("tables_count", 0)
        text_length = docling_page_info.get("text_length", 0)
        
        # Use visual extraction if:
        # 1. Page has figures/charts
        # 2. Low text content (likely image-heavy)
        # 3. Specific pages known to have visual metrics (12, 13)
        page_number = docling_page_info.get("page_number", 0)
        
        should_extract = (
            figures_count > 0 or  # Has figures
            (text_length < 500 and figures_count > 0) or  # Low text + figures
            page_number in [12, 13] or  # Known problem pages
            tables_count > 2  # Many tables (might have embedded charts)
        )
        
        if should_extract:
            logger.info(f"Page {page_number} selected for visual extraction: figures={figures_count}, tables={tables_count}, text_len={text_length}")
        
        return should_extract
