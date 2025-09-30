"""
Integration tests for Chat API endpoints.

Tests the HTTP layer of chat functionality with mocked dependencies.
"""

import pytest
import uuid
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch
from httpx import AsyncClient
from fastapi import FastAPI

from src.main import app
from src.services.chat_service import (
    ChatService, RateLimitExceededError, ChatServiceError
)
from src.models.chat import (
    ChatSession, ChatMessage, ChatSource, MessageRole, 
    MessageStatus, ResponseMode
)


@pytest.fixture
def sample_user_id():
    """Sample user ID for testing."""
    return str(uuid.uuid4())


@pytest.fixture
def sample_organization_id():
    """Sample organization ID for testing."""
    return str(uuid.uuid4())


@pytest.fixture
def sample_session_id():
    """Sample session ID for testing."""
    return str(uuid.uuid4())


@pytest.fixture
def mock_chat_session(sample_session_id, sample_user_id, sample_organization_id):
    """Mock chat session."""
    return ChatSession(
        id=sample_session_id,
        user_id=sample_user_id,
        organization_id=sample_organization_id,
        title="Test Chat",
        is_active=True,
        is_archived=False,
        temperature=0.1,
        model_name="gpt-4o",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        message_count=0
    )


@pytest.fixture
def mock_chat_message(sample_session_id):
    """Mock chat message with sources."""
    return ChatMessage(
        id=str(uuid.uuid4()),
        session_id=sample_session_id,
        role=MessageRole.ASSISTANT,
        content="This is a test response based on the documents.",
        status=MessageStatus.COMPLETED,
        created_at=datetime.utcnow(),
        sources=[
            ChatSource(
                id=str(uuid.uuid4()),
                ragie_document_id="doc-123",
                document_name="Test Document.pdf",
                page_number=1,
                chunk_text="Sample text from document",
                relevance_score=0.95
            )
        ],
        tokens_total=150,
        processing_time_ms=1500
    )


@pytest.fixture
def mock_chat_service():
    """Mock chat service."""
    return AsyncMock(spec=ChatService)


@pytest.fixture
def auth_headers(sample_user_id, sample_organization_id):
    """Authentication headers for requests."""
    return {
        "Authorization": "Bearer test-token",
        "X-Organization-ID": sample_organization_id
    }


class TestChatAPI:
    """Test suite for Chat API endpoints."""
    
    @pytest.mark.asyncio
    async def test_get_active_session_success(
        self, mock_chat_service, mock_chat_session, sample_user_id, sample_organization_id, auth_headers
    ):
        """Test getting active session successfully."""
        # Arrange
        mock_chat_service.get_or_create_active_session.return_value = mock_chat_session
        
        with patch('src.api.chat.get_chat_service', return_value=mock_chat_service), \
             patch('src.api.chat.require_auth', return_value=sample_user_id), \
             patch('src.api.chat.get_organization_id', return_value=sample_organization_id):
            
            async with AsyncClient(app=app, base_url="http://test") as client:
                # Act
                response = await client.get(
                    "/api/v1/chat/session",
                    headers=auth_headers
                )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == mock_chat_session.id
        assert data["title"] == "Test Chat"
        assert data["is_active"] == True
        
        mock_chat_service.get_or_create_active_session.assert_called_once_with(
            user_id=sample_user_id,
            organization_id=sample_organization_id
        )
    
    @pytest.mark.asyncio
    async def test_create_new_session_success(
        self, mock_chat_service, mock_chat_session, sample_user_id, sample_organization_id, auth_headers
    ):
        """Test creating new session successfully."""
        # Arrange
        mock_chat_service.create_new_session.return_value = mock_chat_session
        
        with patch('src.api.chat.get_chat_service', return_value=mock_chat_service), \
             patch('src.api.chat.require_auth', return_value=sample_user_id), \
             patch('src.api.chat.get_organization_id', return_value=sample_organization_id):
            
            async with AsyncClient(app=app, base_url="http://test") as client:
                # Act
                response = await client.post(
                    "/api/v1/chat/session/new",
                    headers=auth_headers
                )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Test Chat"
        
        mock_chat_service.create_new_session.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_send_message_success(
        self, mock_chat_service, mock_chat_message, sample_user_id, 
        sample_organization_id, sample_session_id, auth_headers
    ):
        """Test sending message successfully."""
        # Arrange
        mock_chat_service.send_message.return_value = mock_chat_message
        
        request_data = {
            "question": "What is in the documents?",
            "mode": "strict",
            "model": "gpt-4o"
        }
        
        with patch('src.api.chat.get_chat_service', return_value=mock_chat_service), \
             patch('src.api.chat.require_auth', return_value=sample_user_id), \
             patch('src.api.chat.get_organization_id', return_value=sample_organization_id):
            
            async with AsyncClient(app=app, base_url="http://test") as client:
                # Act
                response = await client.post(
                    f"/api/v1/chat/message?session_id={sample_session_id}",
                    json=request_data,
                    headers=auth_headers
                )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["content"] == "This is a test response based on the documents."
        assert data["role"] == "assistant"
        assert data["status"] == "completed"
        assert len(data["sources"]) == 1
        assert data["sources"][0]["document_name"] == "Test Document.pdf"
        assert data["tokens_total"] == 150
        
        mock_chat_service.send_message.assert_called_once_with(
            session_id=sample_session_id,
            user_id=sample_user_id,
            organization_id=sample_organization_id,
            question="What is in the documents?",
            mode=ResponseMode.STRICT,
            model="gpt-4o"
        )
    
    @pytest.mark.asyncio
    async def test_send_message_rate_limit_exceeded(
        self, mock_chat_service, sample_user_id, sample_organization_id, 
        sample_session_id, auth_headers
    ):
        """Test sending message when rate limit exceeded."""
        # Arrange
        mock_chat_service.send_message.side_effect = RateLimitExceededError(
            "User hourly limit exceeded (50 messages/hour)"
        )
        
        request_data = {
            "question": "Test question",
            "mode": "strict",
            "model": "gpt-4o"
        }
        
        with patch('src.api.chat.get_chat_service', return_value=mock_chat_service), \
             patch('src.api.chat.require_auth', return_value=sample_user_id), \
             patch('src.api.chat.get_organization_id', return_value=sample_organization_id):
            
            async with AsyncClient(app=app, base_url="http://test") as client:
                # Act
                response = await client.post(
                    f"/api/v1/chat/message?session_id={sample_session_id}",
                    json=request_data,
                    headers=auth_headers
                )
        
        # Assert
        assert response.status_code == 429
        data = response.json()
        assert "limit exceeded" in data["detail"].lower()
    
    @pytest.mark.asyncio
    async def test_send_message_validation_error(
        self, sample_user_id, sample_organization_id, sample_session_id, auth_headers
    ):
        """Test sending message with invalid data."""
        # Arrange
        request_data = {
            "question": "",  # Empty question - should fail validation
            "mode": "strict",
            "model": "gpt-4o"
        }
        
        with patch('src.api.chat.require_auth', return_value=sample_user_id), \
             patch('src.api.chat.get_organization_id', return_value=sample_organization_id):
            
            async with AsyncClient(app=app, base_url="http://test") as client:
                # Act
                response = await client.post(
                    f"/api/v1/chat/message?session_id={sample_session_id}",
                    json=request_data,
                    headers=auth_headers
                )
        
        # Assert
        assert response.status_code == 422  # Validation error
    
    @pytest.mark.asyncio
    async def test_get_session_messages_success(
        self, mock_chat_service, mock_chat_message, sample_user_id, 
        sample_session_id, auth_headers
    ):
        """Test getting session messages successfully."""
        # Arrange
        mock_chat_service.get_session_messages.return_value = [mock_chat_message]
        
        with patch('src.api.chat.get_chat_service', return_value=mock_chat_service), \
             patch('src.api.chat.require_auth', return_value=sample_user_id):
            
            async with AsyncClient(app=app, base_url="http://test") as client:
                # Act
                response = await client.get(
                    f"/api/v1/chat/session/{sample_session_id}/messages",
                    headers=auth_headers
                )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["content"] == "This is a test response based on the documents."
        
        mock_chat_service.get_session_messages.assert_called_once_with(
            session_id=sample_session_id,
            limit=50
        )
    
    @pytest.mark.asyncio
    async def test_get_user_sessions_success(
        self, mock_chat_service, mock_chat_session, sample_user_id, auth_headers
    ):
        """Test getting user sessions successfully."""
        # Arrange
        mock_chat_service.get_user_sessions.return_value = [mock_chat_session]
        
        with patch('src.api.chat.get_chat_service', return_value=mock_chat_service), \
             patch('src.api.chat.require_auth', return_value=sample_user_id):
            
            async with AsyncClient(app=app, base_url="http://test") as client:
                # Act
                response = await client.get(
                    "/api/v1/chat/sessions",
                    headers=auth_headers
                )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["title"] == "Test Chat"
        
        mock_chat_service.get_user_sessions.assert_called_once_with(
            user_id=sample_user_id,
            include_archived=False,
            limit=50
        )
    
    @pytest.mark.asyncio
    async def test_archive_session_success(
        self, mock_chat_service, sample_user_id, sample_session_id, auth_headers
    ):
        """Test archiving session successfully."""
        # Arrange
        mock_chat_service.archive_session.return_value = None
        
        with patch('src.api.chat.get_chat_service', return_value=mock_chat_service), \
             patch('src.api.chat.require_auth', return_value=sample_user_id):
            
            async with AsyncClient(app=app, base_url="http://test") as client:
                # Act
                response = await client.post(
                    f"/api/v1/chat/session/{sample_session_id}/archive",
                    headers=auth_headers
                )
        
        # Assert
        assert response.status_code == 204
        mock_chat_service.archive_session.assert_called_once_with(sample_session_id)
    
    @pytest.mark.asyncio
    async def test_delete_session_success(
        self, mock_chat_service, sample_user_id, sample_session_id, auth_headers
    ):
        """Test deleting session successfully."""
        # Arrange
        mock_chat_service.delete_session.return_value = None
        
        with patch('src.api.chat.get_chat_service', return_value=mock_chat_service), \
             patch('src.api.chat.require_auth', return_value=sample_user_id):
            
            async with AsyncClient(app=app, base_url="http://test") as client:
                # Act
                response = await client.delete(
                    f"/api/v1/chat/session/{sample_session_id}",
                    headers=auth_headers
                )
        
        # Assert
        assert response.status_code == 204
        mock_chat_service.delete_session.assert_called_once_with(sample_session_id)
    
    @pytest.mark.asyncio
    async def test_send_message_different_modes(
        self, mock_chat_service, mock_chat_message, sample_user_id,
        sample_organization_id, sample_session_id, auth_headers
    ):
        """Test sending messages with different response modes."""
        # Arrange
        mock_chat_service.send_message.return_value = mock_chat_message
        
        modes = ["strict", "balanced", "creative"]
        
        for mode in modes:
            request_data = {
                "question": "Test question",
                "mode": mode,
                "model": "gpt-4o"
            }
            
            with patch('src.api.chat.get_chat_service', return_value=mock_chat_service), \
                 patch('src.api.chat.require_auth', return_value=sample_user_id), \
                 patch('src.api.chat.get_organization_id', return_value=sample_organization_id):
                
                async with AsyncClient(app=app, base_url="http://test") as client:
                    # Act
                    response = await client.post(
                        f"/api/v1/chat/message?session_id={sample_session_id}",
                        json=request_data,
                        headers=auth_headers
                    )
            
            # Assert
            assert response.status_code == 200
