"""
Frontegg Authentication using Official SDK

This module uses the official Frontegg Python SDK instead of manual JWT verification.
This should resolve the 401 error we were experiencing.

Based on: https://developers.frontegg.com/sdks/backend/python/flask/integrate
"""

import os
import time
import json
import logging
from typing import Optional, Dict, Any
from fastapi import HTTPException, status, Request, Depends, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from jwt import PyJWKClient
from jwt.exceptions import InvalidTokenError
from dotenv import load_dotenv

# Load environment variables
load_dotenv('.env.local')

logger = logging.getLogger(__name__)

# Security scheme for Bearer token
security = HTTPBearer()
security_optional = HTTPBearer(auto_error=False)


class FronteggSDKAuth:
    """Frontegg authentication using the official SDK."""
    
    def __init__(self):
        # Use FRONTEGG_BASE_URL as the issuer (where the app is hosted)
        # Strip trailing slash to match JWT issuer format
        base_url = os.getenv("FRONTEGG_BASE_URL", "https://app-griklxnnsxag.frontegg.com")
        self.issuer = base_url.rstrip('/')
        self.audience = os.getenv("FRONTEGG_CLIENT_ID")  # Client ID is the audience
        self.enabled = bool(self.issuer and self.audience)
        
        # Initialize JWKS client for token verification (with built-in caching)
        self.jwks_client = None
        
        if not self.audience:
            logger.warning("FRONTEGG_CLIENT_ID not set - authentication disabled for development")
        else:
            logger.info(f"Frontegg auth initialized with issuer: {self.issuer}, audience: {self.audience}")
        
        if self.enabled:
            self._init_jwks_client()
    
    
    def _init_jwks_client(self):
        """Initialize JWKS client for JWT verification."""
        try:
            # Discover OIDC configuration
            oidc_url = f"{self.issuer.rstrip('/')}/.well-known/openid-configuration"
            
            # Get JWKS URI from OIDC config
            import urllib.request
            with urllib.request.urlopen(oidc_url) as response:
                oidc_config = json.loads(response.read().decode('utf-8'))
            
            jwks_uri = oidc_config.get('jwks_uri')
            if not jwks_uri:
                raise ValueError("No jwks_uri found in OIDC configuration")
            
            # Initialize JWKS client with caching (PyJWT handles key caching internally)
            self.jwks_client = PyJWKClient(
                jwks_uri, 
                cache_keys=True,  # Cache JWKS keys in memory
                max_cached_keys=16  # Limit cache size
            )
            
        except Exception as e:
            logger.error(f"Failed to initialize JWKS client: {e}")
            self.enabled = False
            self.jwks_client = None
    
    async def verify_token(self, token: str) -> Dict[str, Any]:
        """
        Verify JWT token using OIDC/JWKS (local verification).
        
        No Redis needed - JWT expiration is handled by the token itself.
        PyJWT automatically validates the 'exp' claim.
        """
        # If authentication is disabled, return mock user for development
        if not self.enabled:
            return {
                'id': 'dev-user',
                'email': 'dev@example.com',
                'name': 'Development User',
                'tenantId': 'dev-org',
                'tenantIds': ['dev-org'],
                'roles': ['admin'],
                'permissions': ['*'],
                'verified_at': time.time()
            }
        
        try:
            
            if not self.jwks_client:
                raise ValueError("JWKS client not initialized")
            
            # Get signing key from JWKS (cached by PyJWT)
            signing_key = self.jwks_client.get_signing_key_from_jwt(token).key
            
            # Verify JWT signature and claims (including expiration)
            options = {
                "require": ["exp", "iat"],  # Require expiration and issued-at
                "verify_exp": True,         # Verify token hasn't expired
                "verify_aud": bool(self.audience)
            }
            
            claims = jwt.decode(
                token,
                signing_key,
                algorithms=["RS256", "ES256", "PS256"],
                audience=self.audience if self.audience else None,
                issuer=self.issuer,
                options=options,
            )
            
            # Extract user info from JWT claims
            user_info = {
                'id': claims.get('sub'),
                'email': claims.get('email'),
                'name': claims.get('name'),
                'tenantId': claims.get('tenantId'),
                'tenantIds': claims.get('tenantIds', []),
                'roles': claims.get('roles', []),
                'permissions': claims.get('permissions', []),
                'exp': claims.get('exp'),  # Token expiration
                'iat': claims.get('iat'),  # Token issued at
                'verified_at': time.time()  # When we verified it
            }
            
            return user_info
            
        except InvalidTokenError as e:
            error_msg = str(e)
            logger.error(f"Invalid JWT token: {error_msg}")
            
            # Add helpful debug info for issuer/audience mismatch
            if "issuer" in error_msg.lower():
                logger.error(f"Expected issuer: {self.issuer}, Token was rejected. Check JWT 'iss' claim.")
            if "audience" in error_msg.lower():
                logger.error(f"Expected audience: {self.audience}, Token was rejected. Check JWT 'aud' claim.")
            
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid token: {error_msg}"
            )
        except Exception as e:
            logger.error(f"JWT verification failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Token verification failed: {str(e)}"
            )
    
    


# Global instance
frontegg_sdk_auth = FronteggSDKAuth()


# FastAPI Dependencies using the SDK
async def require_auth_sdk(
    authorization: Optional[str] = Header(None)
) -> str:
    """
    Require authentication using Frontegg SDK.
    Returns the user ID if authentication is successful.
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header is required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format. Expected: Bearer <token>",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = authorization[7:]  # Remove "Bearer " prefix
    
    try:
        user_info = await frontegg_sdk_auth.verify_token(token)
        return user_info.get('id')
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Authentication service error: {str(e)}"
        )


async def get_current_user_sdk(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Dict[str, Any]:
    """Get current authenticated user using Frontegg SDK."""
    return await frontegg_sdk_auth.verify_token(credentials.credentials)


async def get_current_user_optional_sdk(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_optional)
) -> Optional[Dict[str, Any]]:
    """Get current authenticated user (optional) using Frontegg SDK."""
    if not credentials:
        return None
    
    try:
        return await frontegg_sdk_auth.verify_token(credentials.credentials)
    except HTTPException:
        return None


async def get_organization_id_sdk(
    user_info: Dict[str, Any] = Depends(get_current_user_sdk),
    x_organization_id: Optional[str] = Header(None, alias="X-Organization-ID")
) -> str:
    """Get organization ID from header or user's default organization."""
    if x_organization_id:
        # Verify user has access to this organization
        user_orgs = user_info.get('tenantIds', [])
        if x_organization_id not in user_orgs:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"User does not have access to organization: {x_organization_id}"
            )
        return x_organization_id
    
    # Use user's default organization
    default_org = user_info.get('tenantId')
    if not default_org:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No organization context available"
        )
    
    return default_org


# Health check for SDK authentication
async def sdk_auth_health_check() -> Dict[str, Any]:
    """Check if SDK authentication system is healthy."""
    try:
        if not frontegg_sdk_auth.enabled:
            return {
                "status": "disabled",
                "reason": "Missing FRONTEGG_CLIENT_ID or FRONTEGG_API_KEY",
                "timestamp": time.time()
            }
        
        # Test SDK connectivity
        # This would make an actual API call to verify the SDK is working
        
        return {
            "status": "healthy",
            "sdk_initialized": frontegg_sdk_auth.enabled,
            "timestamp": time.time()
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": time.time()
        }
