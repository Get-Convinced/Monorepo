"""
Redis service for caching and temporary storage.

Provides Redis operations for upload progress tracking, caching,
and temporary data storage.
"""

import json
import logging
from typing import Optional, Dict, Any
import redis.asyncio as redis
from ..models.ragie import UploadProgress

logger = logging.getLogger(__name__)


class RedisService:
    """Redis service for caching and temporary storage."""
    
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        """Initialize Redis service. Default port 6379 (standard Redis port)."""
        self.redis_url = redis_url
        self._client: Optional[redis.Redis] = None
    
    async def get_client(self) -> redis.Redis:
        """Get Redis client, creating if needed."""
        if self._client is None:
            self._client = redis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True
            )
        return self._client
    
    async def close(self):
        """Close Redis connection."""
        if self._client:
            await self._client.close()
            self._client = None
    
    # Upload progress tracking
    async def set_upload_progress(self, upload_id: str, progress: UploadProgress) -> None:
        """Store upload progress."""
        try:
            client = await self.get_client()
            key = f"upload_progress:{upload_id}"
            
            # Store as JSON with 1 hour expiration
            await client.setex(
                key,
                3600,  # 1 hour
                progress.model_dump_json()
            )
            
            logger.info(f"Stored upload progress for {upload_id}")
            
        except Exception as e:
            logger.error(f"Failed to store upload progress: {e}")
            # Don't raise - progress tracking is not critical
    
    async def get_upload_progress(self, upload_id: str) -> Optional[UploadProgress]:
        """Get upload progress."""
        try:
            client = await self.get_client()
            key = f"upload_progress:{upload_id}"
            
            data = await client.get(key)
            if not data:
                return None
            
            return UploadProgress.model_validate_json(data)
            
        except Exception as e:
            logger.error(f"Failed to get upload progress: {e}")
            return None
    
    async def delete_upload_progress(self, upload_id: str) -> None:
        """Delete upload progress (cleanup)."""
        try:
            client = await self.get_client()
            key = f"upload_progress:{upload_id}"
            await client.delete(key)
            
        except Exception as e:
            logger.error(f"Failed to delete upload progress: {e}")
    
    # General caching
    async def set_cache(self, key: str, value: Any, ttl_seconds: int = 3600) -> None:
        """Set cache value with TTL."""
        try:
            client = await self.get_client()
            
            # Serialize value to JSON
            if isinstance(value, (dict, list)):
                serialized_value = json.dumps(value)
            else:
                serialized_value = str(value)
            
            await client.setex(key, ttl_seconds, serialized_value)
            
        except Exception as e:
            logger.error(f"Failed to set cache: {e}")
    
    async def get_cache(self, key: str) -> Optional[str]:
        """Get cache value."""
        try:
            client = await self.get_client()
            return await client.get(key)
            
        except Exception as e:
            logger.error(f"Failed to get cache: {e}")
            return None
    
    async def delete_cache(self, key: str) -> None:
        """Delete cache value."""
        try:
            client = await self.get_client()
            await client.delete(key)
            
        except Exception as e:
            logger.error(f"Failed to delete cache: {e}")
    
    # Health check
    async def ping(self) -> bool:
        """Check Redis connection."""
        try:
            client = await self.get_client()
            await client.ping()
            return True
            
        except Exception as e:
            logger.error(f"Redis ping failed: {e}")
            return False


# Global Redis service instance
redis_service = RedisService()


def get_ragie_progress_percentage(status: str) -> int:
    """Convert Ragie status to progress percentage."""
    status_map = {
        "pending": 10,
        "partitioning": 20,
        "partitioned": 30,
        "refined": 50,
        "chunked": 70,
        "indexed": 80,
        "summary_indexed": 90,
        "keyword_indexed": 95,
        "ready": 100,
        "failed": 0
    }
    return status_map.get(status, 0)


def get_stage_description(status: str) -> str:
    """Get human-readable stage description."""
    descriptions = {
        "pending": "Queued for processing",
        "partitioning": "Analyzing document structure",
        "partitioned": "Document structure analyzed",
        "refined": "Extracting content",
        "chunked": "Breaking into searchable chunks",
        "indexed": "Creating search index",
        "summary_indexed": "Generating summaries",
        "keyword_indexed": "Extracting keywords",
        "ready": "Ready for search",
        "failed": "Processing failed"
    }
    return descriptions.get(status, f"Processing ({status})")
