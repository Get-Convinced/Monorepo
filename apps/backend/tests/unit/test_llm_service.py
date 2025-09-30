"""
Unit tests for LLM Service.

Tests OpenAI integration, prompt building, token counting, and error handling.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from openai import OpenAIError

from src.services.llm_service import LLMService, LLMServiceError, TokenLimitExceededError
from src.models.chat import ResponseMode


class TestLLMService:
    """Test suite for LLM Service."""
    
    @pytest.fixture
    def mock_openai_client(self):
        """Create mock OpenAI client."""
        return AsyncMock()
    
    @pytest.fixture
    def llm_service(self, mock_openai_client):
        """Create LLM service with mocked OpenAI client."""
        service = LLMService(api_key="test-key")
        service.client = mock_openai_client
        return service
    
    @pytest.fixture
    def sample_chunks(self):
        """Sample document chunks for testing."""
        return [
            {
                "document_name": "Test Doc 1.pdf",
                "page_number": 1,
                "text": "This is sample text from document 1.",
                "score": 0.95,
                "document_id": "doc-123",
                "chunk_id": "chunk-1"
            },
            {
                "document_name": "Test Doc 2.pdf",
                "page_number": 2,
                "text": "This is sample text from document 2.",
                "score": 0.85,
                "document_id": "doc-456",
                "chunk_id": "chunk-2"
            }
        ]
    
    def test_initialization_with_api_key(self):
        """Test service initialization with API key."""
        service = LLMService(api_key="test-key")
        assert service.api_key == "test-key"
        assert service.client is not None
        assert service.encoding is not None
    
    def test_initialization_without_api_key_raises_error(self):
        """Test service initialization fails without API key."""
        with patch.dict('os.environ', {}, clear=True):
            with pytest.raises(ValueError, match="OPENAI_API_KEY required"):
                LLMService()
    
    def test_build_system_prompt_strict_mode(self, llm_service):
        """Test system prompt for strict mode."""
        prompt = llm_service._build_system_prompt(ResponseMode.STRICT)
        
        assert "helpful AI assistant" in prompt
        assert "provided context" in prompt
        assert "don't have enough information" in prompt
        assert "Do not make assumptions" in prompt
    
    def test_build_system_prompt_balanced_mode(self, llm_service):
        """Test system prompt for balanced mode."""
        prompt = llm_service._build_system_prompt(ResponseMode.BALANCED)
        
        assert "helpful AI assistant" in prompt
        assert "reasonable inferences" in prompt
        assert "clearly state what information is missing" in prompt
    
    def test_build_system_prompt_creative_mode(self, llm_service):
        """Test system prompt for creative mode."""
        prompt = llm_service._build_system_prompt(ResponseMode.CREATIVE)
        
        assert "helpful AI assistant" in prompt
        assert "broader context" in prompt
        assert "general knowledge" in prompt
    
    def test_format_context_with_chunks(self, llm_service, sample_chunks):
        """Test context formatting with document chunks."""
        context = llm_service._format_context(sample_chunks)
        
        assert "Relevant document excerpts" in context
        assert "Test Doc 1.pdf" in context
        assert "Test Doc 2.pdf" in context
        assert "Page 1" in context
        assert "Page 2" in context
        assert "Relevance: 0.95" in context
        assert "Relevance: 0.85" in context
        assert sample_chunks[0]["text"] in context
        assert sample_chunks[1]["text"] in context
    
    def test_format_context_empty_chunks(self, llm_service):
        """Test context formatting with no chunks."""
        context = llm_service._format_context([])
        assert context == "No relevant documents found."
    
    def test_count_tokens(self, llm_service):
        """Test token counting."""
        text = "This is a test sentence."
        token_count = llm_service.count_tokens(text)
        
        # Should be positive integer
        assert isinstance(token_count, int)
        assert token_count > 0
        assert token_count < 100  # Simple sentence shouldn't have many tokens
    
    @pytest.mark.asyncio
    async def test_generate_response_success(self, llm_service, mock_openai_client, sample_chunks):
        """Test successful response generation."""
        # Arrange
        question = "What is in the documents?"
        
        mock_usage = Mock()
        mock_usage.prompt_tokens = 100
        mock_usage.completion_tokens = 50
        mock_usage.total_tokens = 150
        
        mock_choice = Mock()
        mock_choice.message.content = "Based on the documents, this is the answer."
        
        mock_response = Mock()
        mock_response.choices = [mock_choice]
        mock_response.usage = mock_usage
        
        mock_openai_client.chat.completions.create = AsyncMock(return_value=mock_response)
        
        # Act
        result = await llm_service.generate_response(
            question=question,
            chunks=sample_chunks,
            mode=ResponseMode.STRICT,
            model="gpt-4o"
        )
        
        # Assert
        assert result["content"] == "Based on the documents, this is the answer."
        assert result["tokens_prompt"] == 100
        assert result["tokens_completion"] == 50
        assert result["tokens_total"] == 150
        assert result["model"] == "gpt-4o"
        assert result["temperature"] == 0.1  # Strict mode
        assert "processing_time_ms" in result
        
        # Verify OpenAI was called with correct parameters
        mock_openai_client.chat.completions.create.assert_called_once()
        call_args = mock_openai_client.chat.completions.create.call_args
        assert call_args.kwargs["model"] == "gpt-4o"
        assert call_args.kwargs["temperature"] == 0.1
        assert call_args.kwargs["max_tokens"] == 1500
        assert call_args.kwargs["stream"] == False
    
    @pytest.mark.asyncio
    async def test_generate_response_with_conversation_history(
        self, llm_service, mock_openai_client, sample_chunks
    ):
        """Test response generation with conversation history."""
        # Arrange
        question = "Tell me more"
        conversation_history = [
            {"role": "user", "content": "What is X?"},
            {"role": "assistant", "content": "X is Y."}
        ]
        
        mock_usage = Mock()
        mock_usage.prompt_tokens = 100
        mock_usage.completion_tokens = 50
        mock_usage.total_tokens = 150
        
        mock_choice = Mock()
        mock_choice.message.content = "More details about X..."
        
        mock_response = Mock()
        mock_response.choices = [mock_choice]
        mock_response.usage = mock_usage
        
        mock_openai_client.chat.completions.create = AsyncMock(return_value=mock_response)
        
        # Act
        result = await llm_service.generate_response(
            question=question,
            chunks=sample_chunks,
            mode=ResponseMode.BALANCED,
            model="gpt-4o",
            conversation_history=conversation_history
        )
        
        # Assert
        assert result["content"] == "More details about X..."
        assert result["temperature"] == 0.5  # Balanced mode
        
        # Verify history was included in messages
        call_args = mock_openai_client.chat.completions.create.call_args
        messages = call_args.kwargs["messages"]
        assert len(messages) >= 3  # system + history + current
    
    @pytest.mark.asyncio
    async def test_generate_response_different_modes(self, llm_service, mock_openai_client, sample_chunks):
        """Test response generation with different temperature modes."""
        mock_usage = Mock()
        mock_usage.prompt_tokens = 100
        mock_usage.completion_tokens = 50
        mock_usage.total_tokens = 150
        
        mock_choice = Mock()
        mock_choice.message.content = "Response"
        
        mock_response = Mock()
        mock_response.choices = [mock_choice]
        mock_response.usage = mock_usage
        
        mock_openai_client.chat.completions.create = AsyncMock(return_value=mock_response)
        
        # Test each mode
        modes_and_temps = [
            (ResponseMode.STRICT, 0.1),
            (ResponseMode.BALANCED, 0.5),
            (ResponseMode.CREATIVE, 0.9)
        ]
        
        for mode, expected_temp in modes_and_temps:
            result = await llm_service.generate_response(
                question="Test",
                chunks=sample_chunks,
                mode=mode,
                model="gpt-4o"
            )
            
            assert result["temperature"] == expected_temp
    
    @pytest.mark.asyncio
    async def test_generate_response_token_limit_exceeded(self, llm_service, sample_chunks):
        """Test token limit checking."""
        # Create a very long question that would exceed token limit
        question = "Tell me " * 20000  # Very long question
        
        with pytest.raises(TokenLimitExceededError, match="exceed model limit"):
            await llm_service.generate_response(
                question=question,
                chunks=sample_chunks,
                mode=ResponseMode.STRICT,
                model="gpt-3.5-turbo"
            )
    
    @pytest.mark.asyncio
    async def test_generate_response_openai_error(self, llm_service, mock_openai_client, sample_chunks):
        """Test handling of OpenAI API errors."""
        # Arrange
        mock_openai_client.chat.completions.create = AsyncMock(
            side_effect=OpenAIError("API Error")
        )
        
        # Act & Assert
        with pytest.raises(LLMServiceError, match="LLM generation failed"):
            await llm_service.generate_response(
                question="Test",
                chunks=sample_chunks,
                mode=ResponseMode.STRICT,
                model="gpt-4o"
            )
    
    @pytest.mark.asyncio
    async def test_generate_response_unexpected_error(self, llm_service, mock_openai_client, sample_chunks):
        """Test handling of unexpected errors."""
        # Arrange
        mock_openai_client.chat.completions.create = AsyncMock(
            side_effect=Exception("Unexpected error")
        )
        
        # Act & Assert
        with pytest.raises(LLMServiceError, match="Unexpected error"):
            await llm_service.generate_response(
                question="Test",
                chunks=sample_chunks,
                mode=ResponseMode.STRICT,
                model="gpt-4o"
            )
    
    def test_temperature_map_completeness(self, llm_service):
        """Test that all response modes have temperature mappings."""
        for mode in ResponseMode:
            assert mode in llm_service.TEMPERATURE_MAP
            assert 0.0 <= llm_service.TEMPERATURE_MAP[mode] <= 1.0
    
    def test_model_token_limits_defined(self, llm_service):
        """Test that token limits are defined for supported models."""
        assert "gpt-4o" in llm_service.MODEL_TOKEN_LIMITS
        assert "gpt-3.5-turbo" in llm_service.MODEL_TOKEN_LIMITS
        assert llm_service.MODEL_TOKEN_LIMITS["gpt-4o"] > 0
        assert llm_service.MODEL_TOKEN_LIMITS["gpt-3.5-turbo"] > 0
