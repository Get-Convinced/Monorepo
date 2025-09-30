"""
Unit tests for Chat Service.

Tests session management, message processing, RAG orchestration, and rate limiting.
"""

import pytest
import uuid
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession

from src.services.chat_service import (
    ChatService, ChatServiceError, RateLimitExceededError, SessionNotFoundError
)
from src.services.ragie_service import RagieService
from src.services.llm_service import LLMService
from src.models.chat import MessageRole, MessageStatus, ResponseMode
from shared_database.models import ChatSession as DBChatSession, ChatMessage as DBChatMessage


class TestChatService:
    """Test suite for Chat Service."""
    
    @pytest.fixture
    def mock_db_session(self):
        """Create mock database session."""
        session = AsyncMock(spec=AsyncSession)
        session.execute = AsyncMock()
        session.commit = AsyncMock()
        session.refresh = AsyncMock()
        session.add = Mock()
        session.delete = AsyncMock()
        return session
    
    @pytest.fixture
    def mock_ragie_service(self):
        """Create mock Ragie service."""
        return AsyncMock(spec=RagieService)
    
    @pytest.fixture
    def mock_llm_service(self):
        """Create mock LLM service."""
        return AsyncMock(spec=LLMService)
    
    @pytest.fixture
    def chat_service(self, mock_db_session, mock_ragie_service, mock_llm_service):
        """Create chat service with mocked dependencies."""
        return ChatService(
            session=mock_db_session,
            ragie_service=mock_ragie_service,
            llm_service=mock_llm_service
        )
    
    @pytest.fixture
    def sample_user_id(self):
        """Sample user ID."""
        return str(uuid.uuid4())
    
    @pytest.fixture
    def sample_organization_id(self):
        """Sample organization ID."""
        return str(uuid.uuid4())
    
    @pytest.fixture
    def sample_session_id(self):
        """Sample session ID."""
        return str(uuid.uuid4())
    
    # Session Management Tests
    
    @pytest.mark.asyncio
    async def test_get_or_create_active_session_existing(
        self, chat_service, mock_db_session, sample_user_id, sample_organization_id
    ):
        """Test getting existing active session."""
        # Arrange
        existing_session = DBChatSession(
            id=uuid.uuid4(),
            user_id=uuid.UUID(sample_user_id),
            organization_id=uuid.UUID(sample_organization_id),
            title="Existing Chat",
            is_active=True,
            is_archived=False,
            temperature=0.5,
            model_name="gpt-4o",
            max_context_messages=5,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = existing_session
        mock_db_session.execute.return_value = mock_result
        
        # Act
        session = await chat_service.get_or_create_active_session(
            user_id=sample_user_id,
            organization_id=sample_organization_id
        )
        
        # Assert
        assert session.title == "Existing Chat"
        assert session.is_active == True
        assert str(session.user_id) == sample_user_id
    
    @pytest.mark.asyncio
    async def test_get_or_create_active_session_create_new(
        self, chat_service, mock_db_session, sample_user_id, sample_organization_id
    ):
        """Test creating new session when none exists."""
        # Arrange
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db_session.execute.return_value = mock_result
        
        # Mock refresh to set attributes
        async def mock_refresh(obj):
            obj.created_at = datetime.utcnow()
            obj.updated_at = datetime.utcnow()
        
        mock_db_session.refresh = mock_refresh
        
        # Act
        session = await chat_service.get_or_create_active_session(
            user_id=sample_user_id,
            organization_id=sample_organization_id
        )
        
        # Assert
        assert session.title == "New Chat"
        assert session.is_active == True
        assert session.temperature == 0.1  # Default strict mode
        assert session.model_name == "gpt-4o"
        mock_db_session.add.assert_called_once()
        mock_db_session.commit.assert_called()
    
    @pytest.mark.asyncio
    async def test_create_new_session(
        self, chat_service, mock_db_session, sample_user_id, sample_organization_id
    ):
        """Test creating new session and deactivating old one."""
        # Arrange
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db_session.execute.return_value = mock_result
        
        async def mock_refresh(obj):
            obj.created_at = datetime.utcnow()
            obj.updated_at = datetime.utcnow()
        
        mock_db_session.refresh = mock_refresh
        
        # Act
        session = await chat_service.create_new_session(
            user_id=sample_user_id,
            organization_id=sample_organization_id
        )
        
        # Assert
        assert session.is_active == True
        # Should have called execute twice: once for deactivate, once for select
        assert mock_db_session.execute.call_count >= 2
    
    # Rate Limiting Tests
    
    @pytest.mark.asyncio
    async def test_check_rate_limits_within_limits(
        self, chat_service, mock_db_session, sample_user_id, sample_organization_id
    ):
        """Test rate limit check when within limits."""
        # Arrange
        mock_result = Mock()
        mock_result.scalar.return_value = 10  # Well below limits
        mock_db_session.execute.return_value = mock_result
        
        # Act & Assert - should not raise
        await chat_service.check_rate_limits(
            user_id=sample_user_id,
            organization_id=sample_organization_id
        )
    
    @pytest.mark.asyncio
    async def test_check_rate_limits_user_hourly_exceeded(
        self, chat_service, mock_db_session, sample_user_id, sample_organization_id
    ):
        """Test rate limit check when user hourly limit exceeded."""
        # Arrange
        mock_result = Mock()
        mock_result.scalar.return_value = 51  # Over USER_HOURLY_LIMIT (50)
        mock_db_session.execute.return_value = mock_result
        
        # Act & Assert
        with pytest.raises(RateLimitExceededError, match="User hourly limit exceeded"):
            await chat_service.check_rate_limits(
                user_id=sample_user_id,
                organization_id=sample_organization_id
            )
    
    @pytest.mark.asyncio
    async def test_check_rate_limits_org_daily_exceeded(
        self, chat_service, mock_db_session, sample_user_id, sample_organization_id
    ):
        """Test rate limit check when org daily limit exceeded."""
        # Arrange
        # First call (user check) returns 10, second call (org check) returns 1001
        mock_db_session.execute.side_effect = [
            Mock(scalar=Mock(return_value=10)),
            Mock(scalar=Mock(return_value=1001))  # Over ORG_DAILY_LIMIT (1000)
        ]
        
        # Act & Assert
        with pytest.raises(RateLimitExceededError, match="Organization daily limit exceeded"):
            await chat_service.check_rate_limits(
                user_id=sample_user_id,
                organization_id=sample_organization_id
            )
    
    # Message Processing Tests
    
    @pytest.mark.asyncio
    async def test_send_message_success(
        self, chat_service, mock_db_session, mock_ragie_service, mock_llm_service,
        sample_session_id, sample_user_id, sample_organization_id
    ):
        """Test successful message processing with RAG."""
        # Arrange
        question = "What is in the documents?"
        
        # Mock rate limit check (no messages yet)
        mock_db_session.execute.side_effect = [
            Mock(scalar=Mock(return_value=0)),  # User count
            Mock(scalar=Mock(return_value=0)),  # Org count
            Mock(scalars=Mock(return_value=Mock(all=Mock(return_value=[])))),  # History
        ]
        
        # Mock Ragie retrieval
        mock_chunk = Mock()
        mock_chunk.document_id = "doc-123"
        mock_chunk.text = "Sample document text"
        mock_chunk.score = 0.95
        mock_chunk.chunk_id = "chunk-1"
        mock_chunk.metadata = {"page": 1}
        
        mock_retrieval = Mock()
        mock_retrieval.scored_chunks = [mock_chunk]
        mock_ragie_service.retrieve_chunks.return_value = mock_retrieval
        
        # Mock document metadata
        mock_doc = Mock()
        mock_doc.metadata = {"name": "Test Document.pdf"}
        mock_ragie_service.get_document.return_value = mock_doc
        
        # Mock LLM response
        mock_llm_service.generate_response.return_value = {
            "content": "Based on the document, here's the answer.",
            "tokens_prompt": 100,
            "tokens_completion": 50,
            "tokens_total": 150,
            "model": "gpt-4o",
            "temperature": 0.1,
            "processing_time_ms": 1500
        }
        
        # Mock refresh
        async def mock_refresh(obj):
            if isinstance(obj, DBChatMessage):
                obj.created_at = datetime.utcnow()
        
        mock_db_session.refresh = mock_refresh
        
        # Act
        result = await chat_service.send_message(
            session_id=sample_session_id,
            user_id=sample_user_id,
            organization_id=sample_organization_id,
            question=question,
            mode=ResponseMode.STRICT,
            model="gpt-4o"
        )
        
        # Assert
        assert result.content == "Based on the document, here's the answer."
        assert result.role == MessageRole.ASSISTANT
        assert result.status == MessageStatus.COMPLETED
        assert result.tokens_total == 150
        assert len(result.sources) == 1
        assert result.sources[0].document_name == "Test Document.pdf"
        
        # Verify service calls
        mock_ragie_service.retrieve_chunks.assert_called_once()
        mock_llm_service.generate_response.assert_called_once()
        
        # Verify database operations
        assert mock_db_session.add.call_count >= 2  # User message + AI message
        assert mock_db_session.commit.call_count >= 2
    
    @pytest.mark.asyncio
    async def test_send_message_rate_limit_exceeded(
        self, chat_service, mock_db_session, sample_session_id, sample_user_id, sample_organization_id
    ):
        """Test message sending when rate limit exceeded."""
        # Arrange
        mock_db_session.execute.return_value = Mock(scalar=Mock(return_value=51))
        
        # Act & Assert
        with pytest.raises(RateLimitExceededError):
            await chat_service.send_message(
                session_id=sample_session_id,
                user_id=sample_user_id,
                organization_id=sample_organization_id,
                question="Test question",
                mode=ResponseMode.STRICT,
                model="gpt-4o"
            )
    
    @pytest.mark.asyncio
    async def test_send_message_with_conversation_history(
        self, chat_service, mock_db_session, mock_ragie_service, mock_llm_service,
        sample_session_id, sample_user_id, sample_organization_id
    ):
        """Test message processing includes conversation history."""
        # Arrange
        question = "Tell me more"
        
        # Create mock history messages
        past_messages = [
            Mock(role="user", content="What is X?"),
            Mock(role="assistant", content="X is Y.")
        ]
        
        # Mock rate limit check
        mock_db_session.execute.side_effect = [
            Mock(scalar=Mock(return_value=0)),  # User count
            Mock(scalar=Mock(return_value=0)),  # Org count
            Mock(scalars=Mock(return_value=Mock(all=Mock(return_value=past_messages)))),  # History
        ]
        
        # Mock Ragie and LLM
        mock_retrieval = Mock(scored_chunks=[])
        mock_ragie_service.retrieve_chunks.return_value = mock_retrieval
        
        mock_llm_service.generate_response.return_value = {
            "content": "More details...",
            "tokens_prompt": 100,
            "tokens_completion": 50,
            "tokens_total": 150,
            "model": "gpt-4o",
            "temperature": 0.1,
            "processing_time_ms": 1500
        }
        
        async def mock_refresh(obj):
            obj.created_at = datetime.utcnow()
        mock_db_session.refresh = mock_refresh
        
        # Act
        await chat_service.send_message(
            session_id=sample_session_id,
            user_id=sample_user_id,
            organization_id=sample_organization_id,
            question=question,
            mode=ResponseMode.STRICT,
            model="gpt-4o"
        )
        
        # Assert - LLM should have been called with conversation history
        call_args = mock_llm_service.generate_response.call_args
        assert call_args.kwargs["conversation_history"] is not None
        assert len(call_args.kwargs["conversation_history"]) == 2
    
    # Session List/Archive/Delete Tests
    
    @pytest.mark.asyncio
    async def test_get_user_sessions(self, chat_service, mock_db_session, sample_user_id):
        """Test getting user's sessions."""
        # Arrange
        mock_sessions = [
            DBChatSession(
                id=uuid.uuid4(),
                user_id=uuid.UUID(sample_user_id),
                organization_id=uuid.uuid4(),
                title="Chat 1",
                is_active=True,
                is_archived=False,
                temperature=0.1,
                model_name="gpt-4o",
                max_context_messages=5,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
        ]
        
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = mock_sessions
        mock_db_session.execute.return_value = mock_result
        
        # Act
        sessions = await chat_service.get_user_sessions(
            user_id=sample_user_id,
            include_archived=False,
            limit=50
        )
        
        # Assert
        assert len(sessions) == 1
        assert sessions[0].title == "Chat 1"
    
    @pytest.mark.asyncio
    async def test_archive_session(self, chat_service, mock_db_session, sample_session_id):
        """Test archiving a session."""
        # Act
        await chat_service.archive_session(sample_session_id)
        
        # Assert
        mock_db_session.execute.assert_called_once()
        mock_db_session.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_delete_session(self, chat_service, mock_db_session, sample_session_id):
        """Test deleting a session."""
        # Arrange
        mock_session = Mock()
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_session
        mock_db_session.execute.return_value = mock_result
        
        # Act
        await chat_service.delete_session(sample_session_id)
        
        # Assert
        mock_db_session.delete.assert_called_once_with(mock_session)
        mock_db_session.commit.assert_called_once()
    
    # Helper Method Tests
    
    def test_db_session_to_pydantic(self, chat_service):
        """Test conversion from DB session to Pydantic model."""
        # Arrange
        db_session = DBChatSession(
            id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            organization_id=uuid.uuid4(),
            title="Test Chat",
            is_active=True,
            is_archived=False,
            temperature=0.5,
            model_name="gpt-4o",
            max_context_messages=5,
            session_metadata={"test": "data"},
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            last_message_at=datetime.utcnow()
        )
        
        # Act
        pydantic_session = chat_service._db_session_to_pydantic(db_session)
        
        # Assert
        assert pydantic_session.title == "Test Chat"
        assert pydantic_session.is_active == True
        assert pydantic_session.temperature == 0.5
        assert pydantic_session.session_metadata == {"test": "data"}
