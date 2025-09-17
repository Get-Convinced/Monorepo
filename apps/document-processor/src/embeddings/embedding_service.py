"""
Embedding service for managing different providers.
"""

import logging
from typing import List, Optional
from .providers import EmbeddingProvider, OpenAIEmbeddingProvider, OllamaEmbeddingProvider

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Service for managing embedding generation."""
    
    def __init__(self, provider: EmbeddingProvider):
        self.provider = provider
    
    async def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a list of texts."""
        if not texts:
            return []
        
        try:
            return await self.provider.generate_embeddings(texts)
        except Exception as e:
            logger.error(f"Error generating embeddings: {e}")
            raise
    
    @classmethod
    def create_openai_provider(cls, api_key: str, model: str = "text-embedding-3-small") -> 'EmbeddingService':
        """Create an embedding service with OpenAI provider."""
        provider = OpenAIEmbeddingProvider(api_key=api_key, model=model)
        return cls(provider=provider)
    
    @classmethod
    def create_ollama_provider(cls, base_url: str = "http://localhost:11434", model: str = "mxbai-embed-large") -> 'EmbeddingService':
        """Create an embedding service with Ollama provider."""
        provider = OllamaEmbeddingProvider(base_url=base_url, model=model)
        return cls(provider=provider)
