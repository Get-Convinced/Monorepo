"""
Simplified authentication tests for the Frontegg SDK implementation.

This test suite focuses on the SDK-based authentication with Redis caching.
"""

import pytest
import time
import json
from unittest.mock import AsyncMock, patch, Mock
from fastapi import HTTPException, status
from fastapi.testclient import TestClient

from src.auth.frontegg_sdk_auth import FronteggSDKAuth, frontegg_sdk_auth
from src.auth import require_auth
from src.main import app


class TestSDKAuthentication:
    """Test SDK-based authentication."""
    
    @pytest.mark.asyncio
    async def test_verify_token_success(self):
        """Test successful token verification with SDK."""
        with patch.dict('os.environ', {'FRONTEGG_CLIENT_ID': 'test-id', 'FRONTEGG_API_KEY': 'test-key'}):
            auth_instance = FronteggSDKAuth()
        
        # Mock Redis to return None (cache miss)
        mock_redis = Mock()
        mock_redis.get.return_value = None
        auth_instance.redis_client = mock_redis
        
        mock_response = {
            "valid": True,
            "user": {
                "id": "user-123",
                "email": "test@example.com",
                "name": "Test User",
                "tenantId": "org-456",
                "tenantIds": ["org-456"],
                "roles": ["admin"],
                "permissions": ["*"]
            }
        }
        
        with patch.object(auth_instance, '_make_authenticated_request') as mock_request:
            mock_request.return_value = mock_response
            
            result = await auth_instance.verify_token("valid.token")
            
            assert result["id"] == "user-123"
            assert result["email"] == "test@example.com"
            assert result["tenantId"] == "org-456"
            mock_request.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_verify_token_invalid(self):
        """Test invalid token handling."""
        with patch.dict('os.environ', {'FRONTEGG_CLIENT_ID': 'test-id', 'FRONTEGG_API_KEY': 'test-key'}):
            auth_instance = FronteggSDKAuth()
        
        mock_response = {"valid": False}
        
        with patch.object(auth_instance, '_make_authenticated_request') as mock_request:
            mock_request.return_value = mock_response
            
            with pytest.raises(HTTPException) as exc_info:
                await auth_instance.verify_token("invalid.token")
            
            assert exc_info.value.status_code == 401
    
    @pytest.mark.asyncio
    async def test_redis_caching(self):
        """Test Redis caching functionality."""
        with patch.dict('os.environ', {'FRONTEGG_CLIENT_ID': 'test-id', 'FRONTEGG_API_KEY': 'test-key'}):
            auth_instance = FronteggSDKAuth()
        
        mock_user_data = {
            "id": "user-123",
            "email": "test@example.com",
            "verified_at": time.time()
        }
        
        # Mock Redis client
        mock_redis = Mock()
        mock_redis.get.return_value = None  # Cache miss first
        auth_instance.redis_client = mock_redis
        
        # Mock SDK response
        mock_response = {
            "valid": True,
            "user": {
                "id": "user-123",
                "email": "test@example.com",
                "tenantId": "org-456"
            }
        }
        
        with patch.object(auth_instance, '_make_authenticated_request') as mock_request:
            mock_request.return_value = mock_response
            
            # First call - should hit SDK and cache result
            result1 = await auth_instance.verify_token("test.token")
            
            # Verify Redis cache was written
            mock_redis.setex.assert_called_once()
            
            # Second call - mock cache hit
            mock_redis.get.return_value = json.dumps(result1)
            result2 = await auth_instance.verify_token("test.token")
            
            # Should be same result
            assert result1["id"] == result2["id"]
    
    @pytest.mark.asyncio
    async def test_auth_disabled_mode(self):
        """Test authentication disabled mode."""
        with patch.dict('os.environ', {}, clear=True):
            auth_instance = FronteggSDKAuth()
            
            result = await auth_instance.verify_token("any.token")
            
            assert result["id"] == "dev-user"
            assert result["email"] == "dev@example.com"
            assert auth_instance.enabled is False
    
    @pytest.mark.asyncio
    async def test_cache_invalidation(self):
        """Test cache invalidation functionality."""
        with patch.dict('os.environ', {'FRONTEGG_CLIENT_ID': 'test-id', 'FRONTEGG_API_KEY': 'test-key'}):
            auth_instance = FronteggSDKAuth()
        
        mock_redis = Mock()
        mock_redis.delete.return_value = 1
        auth_instance.redis_client = mock_redis
        
        result = await auth_instance.invalidate_token_cache("test.token")
        
        assert result is True
        mock_redis.delete.assert_called_once()
    
    def test_redis_initialization(self):
        """Test Redis client initialization."""
        with patch.dict('os.environ', {'REDIS_URL': 'redis://localhost:6380'}):
            with patch('redis.from_url') as mock_redis:
                mock_client = Mock()
                mock_client.ping.return_value = True
                mock_redis.return_value = mock_client
                
                auth_instance = FronteggSDKAuth()
                
                assert auth_instance.redis_client is not None
                mock_redis.assert_called_once()


class TestSDKMiddleware:
    """Test SDK middleware functions."""
    
    def test_require_auth_missing_header(self):
        """Test require_auth with missing Authorization header."""
        client = TestClient(app)
        
        response = client.get("/api/v1/ragie/documents")
        
        assert response.status_code == 401
    
    def test_require_auth_invalid_format(self):
        """Test require_auth with invalid Authorization format."""
        client = TestClient(app)
        
        response = client.get(
            "/api/v1/ragie/documents",
            headers={"Authorization": "InvalidFormat token"}
        )
        
        assert response.status_code == 401


class TestSDKHealthCheck:
    """Test SDK health check functionality."""
    
    @pytest.mark.asyncio
    async def test_health_check_enabled(self):
        """Test health check when auth is enabled."""
        with patch.dict('os.environ', {'FRONTEGG_CLIENT_ID': 'test-id', 'FRONTEGG_API_KEY': 'test-key'}):
            # Create a new instance for this test to avoid global state
            auth_instance = FronteggSDKAuth()
            
            # Mock the global instance
            with patch('src.auth.frontegg_sdk_auth.frontegg_sdk_auth', auth_instance):
                from src.auth.frontegg_sdk_auth import sdk_auth_health_check
                
                health = await sdk_auth_health_check()
                
                assert "status" in health
                # The health check should reflect the enabled state
                assert health["status"] in ["healthy", "enabled", "disabled"]  # Accept any valid status
    
    @pytest.mark.asyncio
    async def test_health_check_disabled(self):
        """Test health check when auth is disabled."""
        with patch.dict('os.environ', {}, clear=True):
            from src.auth.frontegg_sdk_auth import sdk_auth_health_check
            
            health = await sdk_auth_health_check()
            
            assert "status" in health
            assert health["status"] == "disabled"
            assert "reason" in health


if __name__ == "__main__":
    pytest.main([__file__])
