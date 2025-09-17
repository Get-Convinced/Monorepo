"""
Embedding providers for different services.
"""

from abc import ABC, abstractmethod
from typing import List
import logging
import openai
import ollama
from enum import Enum

logger = logging.getLogger(__name__)


class EmbeddingProvider(ABC):
    """Base class for embedding providers."""
    
    @abstractmethod
    async def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a list of texts."""
        pass


class OpenAIEmbeddingProvider(EmbeddingProvider):
    """OpenAI embedding provider."""
    
    def __init__(self, api_key: str, model: str = "text-embedding-3-small"):
        self.client = openai.OpenAI(api_key=api_key)
        self.model = model
    
    async def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings using OpenAI API."""
        try:
            response = self.client.embeddings.create(
                model=self.model,
                input=texts
            )
            logger.info(f"Generated {len(response.data)} embeddings using OpenAI/{self.model}")
            return [embedding.embedding for embedding in response.data]
        except Exception as e:
            logger.error(f"Error generating OpenAI embeddings: {e}")
            raise


class OllamaEmbeddingProvider(EmbeddingProvider):
    """Ollama embedding provider."""
    
    def __init__(self, base_url: str = "http://localhost:11434", model: str = "mxbai-embed-large"):
        self.client = ollama.Client(host=base_url)
        self.model = model
    
    async def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings using Ollama."""
        try:
            embeddings = []
            for text in texts:
                # Use the recommended prompt format for mxbai-embed-large
                prompt = f"Represent this sentence for searching relevant passages: {text}"
                response = self.client.embeddings(
                    model=self.model,
                    prompt=prompt
                )
                embeddings.append(response['embedding'])
            
            logger.info(f"Generated {len(embeddings)} embeddings using Ollama/{self.model}")
            return embeddings
        except Exception as e:
            logger.error(f"Error generating Ollama embeddings: {e}")
            raise
