"""
Global test configuration and fixtures.

Simplified and consolidated test fixtures for the backend test suite.
"""
import pytest
import asyncio
from typing import AsyncGenerator
from unittest.mock import Mock, patch
from httpx import AsyncClient
from fastapi.testclient import TestClient

from src.main import app
from src.auth import frontegg_sdk_auth


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def test_client() -> AsyncGenerator[AsyncClient, None]:
    """Create async test client for FastAPI app."""
    async with AsyncClient(app=app, base_url="http://testserver") as client:
        yield client


@pytest.fixture
def sync_test_client() -> TestClient:
    """Create synchronous test client for FastAPI app."""
    return TestClient(app)


@pytest.fixture
def mock_redis():
    """Mock Redis client for testing cache functionality."""
    mock_redis = Mock()
    mock_redis.get.return_value = None
    mock_redis.setex.return_value = True
    mock_redis.delete.return_value = True
    mock_redis.ping.return_value = True
    return mock_redis


@pytest.fixture
def valid_auth_headers():
    """Create valid authentication headers."""
    return {
        "Authorization": "Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.valid_payload.signature",
        "Content-Type": "application/json"
    }


@pytest.fixture
def invalid_auth_headers():
    """Create invalid authentication headers."""
    return {
        "Authorization": "Bearer invalid-token",
        "Content-Type": "application/json"
    }


@pytest.fixture
def no_auth_headers():
    """Create headers without authentication."""
    return {
        "Content-Type": "application/json"
    }


@pytest.fixture(autouse=True)
def setup_test_environment(mock_redis):
    """Set up clean test environment before each test."""
    # Mock Redis client in auth
    with patch.object(frontegg_sdk_auth, 'redis_client', mock_redis):
        yield