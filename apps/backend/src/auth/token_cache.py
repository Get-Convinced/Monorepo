"""
JWT Token Caching System for Performance Optimization
"""
import json
import os
import time
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import redis
import jwt
from functools import lru_cache

class TokenCache:
    """Smart token caching with fallback to Frontegg validation."""
    
    def __init__(self, redis_client: Optional[redis.Redis] = None):
        self.redis_client = redis_client
        self.local_cache = {}  # In-memory fallback
        self.cache_ttl = 300  # 5 minutes default
        self.public_key_cache_ttl = 3600  # 1 hour for public key
        
        # Initialize Redis if available
        if not self.redis_client:
            try:
                redis_url = os.getenv("REDIS_URL", "redis://localhost:6380")
                self.redis_client = redis.from_url(redis_url, decode_responses=True)
                # Test connection
                self.redis_client.ping()
            except Exception:
                self.redis_client = None  # Fall back to local cache only
    
    async def get_cached_user(self, token: str) -> Optional[Dict[str, Any]]:
        """Get user from cache if token is valid and not expired."""
        cache_key = f"token:{self._hash_token(token)}"
        
        # Try Redis first
        if self.redis_client:
            try:
                cached_data = self.redis_client.get(cache_key)
                if cached_data:
                    data = json.loads(cached_data)
                    if self._is_token_valid_locally(data.get('token'), data.get('expires_at')):
                        return data.get('user')
            except Exception:
                pass  # Fall back to local cache
        
        # Try local cache
        if cache_key in self.local_cache:
            data = self.local_cache[cache_key]
            if self._is_token_valid_locally(data.get('token'), data.get('expires_at')):
                return data.get('user')
        
        return None
    
    async def cache_user_token(self, token: str, user: Dict[str, Any], expires_at: float):
        """Cache user data with token expiration."""
        cache_key = f"token:{self._hash_token(token)}"
        cache_data = {
            'user': user,
            'token': token,
            'expires_at': expires_at,
            'cached_at': time.time()
        }
        
        # Cache in Redis
        if self.redis_client:
            try:
                self.redis_client.setex(
                    cache_key, 
                    self.cache_ttl, 
                    json.dumps(cache_data)
                )
            except Exception:
                pass  # Fall back to local cache
        
        # Cache locally as fallback
        self.local_cache[cache_key] = cache_data
        
        # Clean up expired local cache entries
        self._cleanup_local_cache()
    
    def invalidate_token(self, token: str):
        """Invalidate a specific token from cache."""
        cache_key = f"token:{self._hash_token(token)}"
        
        if self.redis_client:
            try:
                self.redis_client.delete(cache_key)
            except Exception:
                pass
        
        self.local_cache.pop(cache_key, None)
    
    def invalidate_user_tokens(self, user_id: str):
        """Invalidate all tokens for a specific user."""
        # This would require storing user_id -> token mappings
        # For now, we'll rely on TTL expiration
        pass
    
    def _hash_token(self, token: str) -> str:
        """Create a hash of the token for cache key."""
        import hashlib
        return hashlib.sha256(token.encode()).hexdigest()[:16]
    
    def _is_token_valid_locally(self, token: str, expires_at: float) -> bool:
        """Check if token is still valid without network call."""
        if not token or not expires_at:
            return False
        
        # Check if token is expired
        if time.time() > expires_at:
            return False
        
        # Basic JWT structure validation (without signature verification)
        try:
            # Decode without verification to check structure
            payload = jwt.decode(token, options={"verify_signature": False})
            return payload.get('exp', 0) > time.time()
        except:
            return False
    
    def _cleanup_local_cache(self):
        """Remove expired entries from local cache."""
        current_time = time.time()
        expired_keys = [
            key for key, data in self.local_cache.items()
            if data.get('expires_at', 0) < current_time
        ]
        for key in expired_keys:
            self.local_cache.pop(key, None)

# Global cache instance
token_cache = TokenCache()
