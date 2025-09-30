"""
Unit tests for Ragie HTTP client.

Following TDD principles - these tests define the expected behavior
of the RagieClient before implementation.
"""

import pytest
from unittest.mock import AsyncMock, Mock
import httpx
import respx
from freezegun import freeze_time
from datetime import datetime

from src.adapters.ragie_client import RagieClient, RagieError, RagieAuthError, RagieNotFoundError
from src.models.ragie import (
    RagieDocument, 
    RagieDocumentStatus,
    RagieRetrievalResult,
    RagieChunk
)


class TestRagieClient:
    """Test suite for RagieClient."""
    
    @pytest.fixture
    def ragie_client(self):
        """Create RagieClient with test configuration."""
        return RagieClient(
            api_key="test-api-key",
            base_url="https://api.ragie.ai"
        )
    
    @pytest.fixture
    def mock_document_response(self):
        """Mock Ragie document response."""
        return {
            "id": "doc-123",
            "name": "test-document.pdf",
            "status": "ready",
            "created_at": "2024-01-15T12:00:00Z",
            "updated_at": "2024-01-15T12:05:00Z",
            "metadata": {
                "title": "Test Document",
                "tags": ["important", "research"]
            }
        }
    
    @pytest.fixture
    def mock_retrieval_response(self):
        """Mock Ragie retrieval response."""
        return {
            "scored_chunks": [
                {
                    "chunk": {
                        "id": "chunk-1",
                        "document_id": "doc-123",
                        "text": "This is relevant content from the document.",
                        "metadata": {"page": 1}
                    },
                    "score": 0.95
                },
                {
                    "chunk": {
                        "id": "chunk-2", 
                        "document_id": "doc-456",
                        "text": "Another relevant piece of information.",
                        "metadata": {"page": 2}
                    },
                    "score": 0.87
                }
            ]
        }

    @pytest.mark.asyncio
    async def test_upload_document_success(self, ragie_client, mock_document_response):
        """Test successful document upload to Ragie."""
        # Arrange
        file_content = b"fake pdf content"
        filename = "test.pdf"
        partition = "org-123"
        metadata = {"title": "Test Document", "tags": ["research"]}
        
        with respx.mock:
            respx.post("https://api.ragie.ai/documents").mock(
                return_value=httpx.Response(201, json=mock_document_response)
            )
            
            # Act
            result = await ragie_client.upload_document(
                file_content=file_content,
                filename=filename,
                partition=partition,
                metadata=metadata
            )
            
            # Assert
            assert isinstance(result, RagieDocument)
            assert result.id == "doc-123"
            assert result.name == "test-document.pdf"
            assert result.status == RagieDocumentStatus.READY
            assert result.metadata["title"] == "Test Document"
            assert "research" in result.metadata["tags"]

    @pytest.mark.asyncio
    async def test_upload_document_authentication_error(self, ragie_client):
        """Test document upload with invalid API key."""
        # Arrange
        file_content = b"fake pdf content"
        filename = "test.pdf"
        partition = "org-123"
        
        with respx.mock:
            respx.post("https://api.ragie.ai/documents").mock(
                return_value=httpx.Response(401, json={"error": "Unauthorized"})
            )
            
            # Act & Assert
            with pytest.raises(RagieAuthError) as exc_info:
                await ragie_client.upload_document(
                    file_content=file_content,
                    filename=filename,
                    partition=partition
                )
            
            assert "Unauthorized" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_list_documents_success(self, ragie_client, mock_document_response):
        """Test successful document listing with pagination."""
        # Arrange
        partition = "org-123"
        limit = 10
        cursor = None
        
        mock_list_response = {
            "documents": [mock_document_response],
            "cursor": "next-cursor-123",
            "has_more": True
        }
        
        with respx.mock:
            respx.get("https://api.ragie.ai/documents").mock(
                return_value=httpx.Response(200, json=mock_list_response)
            )
            
            # Act
            result = await ragie_client.list_documents(
                partition=partition,
                limit=limit,
                cursor=cursor
            )
            
            # Assert
            assert len(result.documents) == 1
            assert isinstance(result.documents[0], RagieDocument)
            assert result.documents[0].id == "doc-123"
            assert result.cursor == "next-cursor-123"
            assert result.has_more is True

    @pytest.mark.asyncio
    async def test_get_document_success(self, ragie_client, mock_document_response):
        """Test successful document retrieval by ID."""
        # Arrange
        document_id = "doc-123"
        partition = "org-123"
        
        with respx.mock:
            respx.get(f"https://api.ragie.ai/documents/{document_id}").mock(
                return_value=httpx.Response(200, json=mock_document_response)
            )
            
            # Act
            result = await ragie_client.get_document(
                document_id=document_id,
                partition=partition
            )
            
            # Assert
            assert isinstance(result, RagieDocument)
            assert result.id == "doc-123"
            assert result.name == "test-document.pdf"

    @pytest.mark.asyncio
    async def test_get_document_not_found(self, ragie_client):
        """Test document retrieval when document doesn't exist."""
        # Arrange
        document_id = "nonexistent-doc"
        partition = "org-123"
        
        with respx.mock:
            respx.get(f"https://api.ragie.ai/documents/{document_id}").mock(
                return_value=httpx.Response(404, json={"error": "Document not found"})
            )
            
            # Act & Assert
            with pytest.raises(RagieNotFoundError) as exc_info:
                await ragie_client.get_document(
                    document_id=document_id,
                    partition=partition
                )
            
            assert "Document not found" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_delete_document_success(self, ragie_client):
        """Test successful document deletion."""
        # Arrange
        document_id = "doc-123"
        partition = "org-123"
        
        with respx.mock:
            respx.delete(f"https://api.ragie.ai/documents/{document_id}").mock(
                return_value=httpx.Response(204)
            )
            
            # Act
            await ragie_client.delete_document(
                document_id=document_id,
                partition=partition
            )
            
            # Assert - No exception should be raised

    @pytest.mark.asyncio
    async def test_update_document_metadata_success(self, ragie_client, mock_document_response):
        """Test successful document metadata update."""
        # Arrange
        document_id = "doc-123"
        partition = "org-123"
        metadata = {"title": "Updated Title", "tags": ["updated", "metadata"]}
        
        updated_response = {**mock_document_response, "metadata": metadata}
        
        with respx.mock:
            respx.patch(f"https://api.ragie.ai/documents/{document_id}/metadata").mock(
                return_value=httpx.Response(200, json=updated_response)
            )
            
            # Act
            result = await ragie_client.update_document_metadata(
                document_id=document_id,
                partition=partition,
                metadata=metadata
            )
            
            # Assert
            assert isinstance(result, RagieDocument)
            assert result.metadata["title"] == "Updated Title"
            assert "updated" in result.metadata["tags"]

    @pytest.mark.asyncio
    async def test_retrieve_chunks_success(self, ragie_client, mock_retrieval_response):
        """Test successful chunk retrieval for RAG."""
        # Arrange
        query = "What is the main topic of the document?"
        partition = "org-123"
        max_chunks = 5
        
        with respx.mock:
            respx.post("https://api.ragie.ai/retrievals").mock(
                return_value=httpx.Response(200, json=mock_retrieval_response)
            )
            
            # Act
            result = await ragie_client.retrieve_chunks(
                query=query,
                partition=partition,
                max_chunks=max_chunks
            )
            
            # Assert
            assert isinstance(result, RagieRetrievalResult)
            assert len(result.chunks) == 2
            
            chunk1 = result.chunks[0]
            assert isinstance(chunk1, RagieChunk)
            assert chunk1.id == "chunk-1"
            assert chunk1.document_id == "doc-123"
            assert chunk1.score == 0.95
            assert "relevant content" in chunk1.text

    @pytest.mark.asyncio
    async def test_retrieve_chunks_with_filters(self, ragie_client, mock_retrieval_response):
        """Test chunk retrieval with document ID filters."""
        # Arrange
        query = "specific information"
        partition = "org-123"
        document_ids = ["doc-123", "doc-456"]
        
        with respx.mock:
            respx.post("https://api.ragie.ai/retrievals").mock(
                return_value=httpx.Response(200, json=mock_retrieval_response)
            )
            
            # Act
            result = await ragie_client.retrieve_chunks(
                query=query,
                partition=partition,
                document_ids=document_ids
            )
            
            # Assert
            assert isinstance(result, RagieRetrievalResult)
            assert len(result.chunks) == 2

    @pytest.mark.asyncio
    async def test_get_document_source_success(self, ragie_client):
        """Test successful document source file retrieval."""
        # Arrange
        document_id = "doc-123"
        partition = "org-123"
        mock_file_content = b"original file content"
        
        with respx.mock:
            respx.get(f"https://api.ragie.ai/documents/{document_id}/source").mock(
                return_value=httpx.Response(
                    200, 
                    content=mock_file_content,
                    headers={"content-type": "application/pdf"}
                )
            )
            
            # Act
            content, content_type = await ragie_client.get_document_source(
                document_id=document_id,
                partition=partition
            )
            
            # Assert
            assert content == mock_file_content
            assert content_type == "application/pdf"

    @pytest.mark.asyncio
    async def test_request_headers_include_auth_and_partition(self, ragie_client):
        """Test that all requests include proper authentication and partition headers."""
        # Arrange
        partition = "org-123"
        
        with respx.mock as respx_mock:
            route = respx.get("https://api.ragie.ai/documents").mock(
                return_value=httpx.Response(200, json={"documents": []})
            )
            
            # Act
            await ragie_client.list_documents(partition=partition)
            
            # Assert
            request = route.calls[0].request
            assert request.headers["Authorization"] == "Bearer test-api-key"
            assert request.headers["partition"] == "org-123"

    @pytest.mark.asyncio
    async def test_server_error_handling(self, ragie_client):
        """Test server error handling (no retry logic implemented yet)."""
        # Arrange
        partition = "org-123"
        
        with respx.mock:
            respx.get("https://api.ragie.ai/documents").mock(
                return_value=httpx.Response(500, json={"error": "Internal Server Error"})
            )
            
            # Act & Assert - Should fail immediately (no retry)
            with pytest.raises(RagieError) as exc_info:
                await ragie_client.list_documents(partition=partition)
            
            assert "Internal Server Error" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_timeout_handling(self, ragie_client):
        """Test proper timeout handling (no retry logic implemented yet)."""
        # Arrange
        partition = "org-123"
        
        with respx.mock:
            respx.get("https://api.ragie.ai/documents").mock(
                side_effect=httpx.TimeoutException("Request timed out")
            )
            
            # Act & Assert - Should fail immediately (no retry)
            with pytest.raises(RagieError) as exc_info:
                await ragie_client.list_documents(partition=partition)
            
            assert "timeout" in str(exc_info.value).lower()

    def test_client_initialization_with_invalid_config(self):
        """Test client initialization with invalid configuration."""
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            RagieClient(api_key="", base_url="https://api.ragie.ai")
        
        assert "API key is required" in str(exc_info.value)
        
        with pytest.raises(ValueError) as exc_info:
            RagieClient(api_key="valid-key", base_url="")
        
        assert "Base URL is required" in str(exc_info.value)
