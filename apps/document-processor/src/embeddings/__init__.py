"""
Embedding generation and management.
"""

from .embedding_service import EmbeddingService
from .providers import EmbeddingProvider, OpenAIEmbeddingProvider, OllamaEmbeddingProvider

__all__ = [
    "EmbeddingService",
    "EmbeddingProvider",
    "OpenAIEmbeddingProvider", 
    "OllamaEmbeddingProvider"
]
