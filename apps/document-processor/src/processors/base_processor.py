"""
Base document processor class.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class BaseDocumentProcessor(ABC):
    """Base class for document processors."""
    
    def __init__(self):
        self.supported_extensions = []
    
    @abstractmethod
    def extract_text(self, file_path: str) -> str:
        """Extract text content from document."""
        pass
    
    @abstractmethod
    def extract_metadata(self, file_path: str) -> Dict[str, Any]:
        """Extract metadata from document."""
        pass
    
    def can_process(self, file_path: str) -> bool:
        """Check if this processor can handle the given file."""
        file_ext = Path(file_path).suffix.lower()
        return file_ext in self.supported_extensions
    
    def process_document(self, file_path: str) -> Dict[str, Any]:
        """Process document and return extracted content and metadata."""
        try:
            if not self.can_process(file_path):
                raise ValueError(f"Unsupported file type: {Path(file_path).suffix}")
            
            text_content = self.extract_text(file_path)
            metadata = self.extract_metadata(file_path)
            
            return {
                "content": text_content,
                "metadata": metadata,
                "file_path": file_path,
                "processor": self.__class__.__name__
            }
            
        except Exception as e:
            logger.error(f"Error processing document {file_path}: {e}")
            raise
