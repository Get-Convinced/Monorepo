"""
Document processors for different file types.
"""

from .base_processor import BaseDocumentProcessor
from .docling_processor import DoclingProcessor

__all__ = [
    "BaseDocumentProcessor",
    "DoclingProcessor"
]
