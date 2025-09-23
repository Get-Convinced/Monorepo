"""
Frontegg Authentication Middleware for FastAPI Backend
"""
import os
import jwt
import httpx
from typing import Optional, Dict, Any
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from functools import lru_cache
from .token_cache import token_cache

# Security scheme for Bearer token
security = HTTPBearer()

class FronteggAuth:
    def __init__(self):
        self.client_id = os.getenv("FRONTEGG_CLIENT_ID")
        self.client_secret = os.getenv("FRONTEGG_CLIENT_SECRET")
        self.base_url = os.getenv("FRONTEGG_BASE_URL", "https://app.frontegg.com")
        self.public_key = None
    
    @lru_cache(maxsize=1)
    async def get_public_key(self) -> str:
        """Get Frontegg public key for JWT verification"""
        if self.public_key:
            return self.public_key
            
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/frontegg/identity/resources/configurations/v1"
                )
                response.raise_for_status()
                config = response.json()
                self.public_key = config.get("publicKey")
                return self.public_key
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get Frontegg public key: {str(e)}"
            )
    
    async def verify_token(self, token: str) -> Dict[str, Any]:
        """Verify Frontegg JWT token with caching for performance"""
        # First, try to get from cache
        cached_user = await token_cache.get_cached_user(token)
        if cached_user:
            return cached_user
        
        # If not in cache, verify with Frontegg
        try:
            public_key = await self.get_public_key()
            
            # Decode and verify the JWT token
            payload = jwt.decode(
                token,
                public_key,
                algorithms=["RS256"],
                audience=self.client_id,
                issuer=self.base_url
            )
            
            # Cache the result for future requests
            expires_at = payload.get('exp', 0)
            await token_cache.cache_user_token(token, payload, expires_at)
            
            return payload
            
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired"
            )
        except jwt.InvalidTokenError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid token: {str(e)}"
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Token verification failed: {str(e)}"
            )

# Global instance
frontegg_auth = FronteggAuth()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Dict[str, Any]:
    """Dependency to get current authenticated user"""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials not provided"
        )
    
    token = credentials.credentials
    user_info = await frontegg_auth.verify_token(token)
    
    return user_info

async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[Dict[str, Any]]:
    """Optional dependency to get current user (for public endpoints)"""
    if not credentials:
        return None
    
    try:
        token = credentials.credentials
        user_info = await frontegg_auth.verify_token(token)
        return user_info
    except HTTPException:
        return None
